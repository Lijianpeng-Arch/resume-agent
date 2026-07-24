#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI简历优化Agent - 本地网站版后端
=================================
纯 Python 标准库实现（http.server / json / urllib / threading / socket / webbrowser / os / sys）
无第三方依赖，Python 3.7+ 直接运行。

功能：
- 静态服务（GET / 返回 index.html）
- /api/status  查询运行模式
- /api/config  GET/POST 配置管理（api_key 脱敏返回）
- /api/detect  自动识别 API Key 所属厂商
- /api/test    测试当前配置可用性
- /api/generate 核心功能：JD+简历 → 匹配度分析+优化（LLM模式 / 离线规则引擎降级）
"""

import json
import os
import re
import sys
import threading
import time
import urllib.request
import urllib.error
import webbrowser


def open_app_window(url):
    """以应用窗口模式打开页面：免疫浏览器"恢复上次会话"设置，永远只开一个干净窗口。
    优先 Edge / Chrome 的 --app 模式；都找不到时回退系统默认浏览器。"""
    import subprocess
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for exe in candidates:
        try:
            if os.path.exists(exe):
                subprocess.Popen([exe, "--app=" + url])
                return
        except Exception:
            continue
    try:
        webbrowser.open(url)
    except Exception:
        pass
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
# 引入离线规则引擎所在目录（../code/resume_agent.py）
CODE_DIR = os.path.join(os.path.dirname(BASE_DIR), "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

# 已知厂商（全部 OpenAI 兼容接口格式）
PROVIDERS = [
    {"name": "DeepSeek",      "base_url": "https://api.deepseek.com/v1"},
    {"name": "Moonshot Kimi", "base_url": "https://api.moonshot.cn/v1"},
    {"name": "智谱GLM",       "base_url": "https://open.bigmodel.cn/api/paas/v4"},
    {"name": "通义千问",      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    {"name": "MiniMax",       "base_url": "https://api.minimaxi.com/v1"},
    {"name": "MiniMax(国际版)", "base_url": "https://api.minimax.io/v1"},
    {"name": "OpenAI",        "base_url": "https://api.openai.com/v1"},
]

# ==============================================================================
# 配置读写
# ==============================================================================

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def mask_key(key):
    """API Key 脱敏：只显示前4后4位"""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


# ==============================================================================
# HTTP 工具
# ==============================================================================

def http_request(url, method="GET", payload=None, headers=None, timeout=10):
    """统一 HTTP 请求封装，返回 (status_code, dict_or_text) 或抛出异常"""
    data = None
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        try:
            return resp.status, json.loads(body)
        except Exception:
            return resp.status, body


def friendly_http_error(e):
    """把网络/HTTP异常转成人类可读的中文提示"""
    if isinstance(e, urllib.error.HTTPError):
        code = e.code
        if code == 401:
            return "API Key 无效或已过期（401 未授权），请检查 Key 是否正确"
        if code == 403:
            return "访问被拒绝（403），该 Key 可能没有此接口权限"
        if code == 429:
            return "请求过于频繁或额度不足（429 限流），请稍后再试或检查账户余额"
        if 500 <= code < 600:
            return "厂商服务器异常（%d），请稍后再试" % code
        return "HTTP 请求失败（状态码 %d）" % code
    if isinstance(e, urllib.error.URLError):
        reason = getattr(e, "reason", e)
        return "网络连接失败：%s（请检查网络或代理设置）" % reason
    if isinstance(e, TimeoutError) or "timed out" in str(e):
        return "请求超时，请检查网络后重试"
    return "请求失败：%s" % e


# ==============================================================================
# LLM 调用
# ==============================================================================

def call_llm(system_prompt, user_prompt, max_tokens=4000):
    """
    调用 OpenAI 兼容的 chat/completions 接口。
    返回 (ok, content_or_errmsg)
    """
    cfg = load_config()
    api_key = cfg.get("api_key", "")
    base_url = cfg.get("base_url", "").rstrip("/")
    model = cfg.get("model", "")
    if not api_key or not base_url or not model:
        return False, "LLM 配置不完整（缺少 api_key / base_url / model）"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    try:
        status, data = http_request(
            base_url + "/chat/completions",
            method="POST",
            payload=payload,
            headers={"Authorization": "Bearer " + api_key},
            timeout=300,
        )
        content = data["choices"][0]["message"]["content"]
        # 思考型模型（MiniMax-M系列 / DeepSeek-R1 等）会附带 <think> 思考块（可能被max_tokens截断不闭合），统一剥离
        content = re.sub(r"<think>.*?(</think>|$)", "", content, flags=re.S).strip()
        return True, content
    except Exception as e:
        err_msg = friendly_http_error(e)
        # 部分模型 max_tokens 上限较低（如 DeepSeek 8192）：超限被拒时自动降档重试一次
        if max_tokens and max_tokens > 4096 and ("max_tokens" in (str(e) + err_msg).lower()):
            payload["max_tokens"] = max_tokens // 2
            try:
                status, data = http_request(
                    base_url + "/chat/completions",
                    method="POST",
                    payload=payload,
                    headers={"Authorization": "Bearer " + api_key},
                    timeout=300,
                )
                content = data["choices"][0]["message"]["content"]
                content = re.sub(r"<think>.*?(</think>|$)", "", content, flags=re.S).strip()
                return True, content
            except Exception as e2:
                return False, friendly_http_error(e2)
        return False, err_msg


# ==============================================================================
# 离线规则引擎
# ==============================================================================

def offline_generate(jd_text, resume_text):
    """调用 code/resume_agent.py 里的规则引擎类，输出与 LLM 模式同构的结果"""
    try:
        import importlib
        import resume_agent
        importlib.reload(resume_agent)
    except Exception as e:
        return None, "离线规则引擎加载失败：%s" % e

    try:
        jd_parsed = resume_agent.JDParser.parse(jd_text)
        resume_parsed = resume_agent.ResumeParser.parse(resume_text)
        match = resume_agent.MatchEngine.calculate(jd_parsed, resume_parsed)
        opt = resume_agent.ResumeOptimizer.optimize(jd_parsed, resume_parsed, match)

        bd = match["breakdown"]
        dim_names = {
            "skill_coverage": "技能覆盖",
            "experience_match": "经验匹配",
            "education_match": "学历匹配",
            "project_richness": "项目丰富度",
            "skill_relevance": "技能相关度",
        }
        dimensions = []
        for key, val in bd.items():
            detail = ""
            d = val.get("details")
            if isinstance(d, dict):
                if key == "skill_coverage":
                    detail = "覆盖率 %s%%" % d.get("rate", 0)
                elif key == "experience_match":
                    detail = "要求%s年 / 实际约%s年（%s）" % (
                        d.get("required", 0), d.get("actual", 0), d.get("status", ""))
                elif key == "education_match":
                    detail = "要求%s / 实际%s（%s）" % (
                        d.get("required", "无"), d.get("actual", "未知"), d.get("status", ""))
            dimensions.append({
                "name": dim_names.get(key, key),
                "score": val["score"],
                "max": val["max"],
                "detail": detail,
            })

        return {
            "match_score": match["total_score"],
            "score_level": match["score_level"],
            "job_title": jd_parsed.get("title", ""),
            "candidate_name": resume_parsed.get("name", ""),
            "dimensions": dimensions,
            "matched_skills": match.get("matched_skills", []),
            "missing_skills": match.get("missing_skills", []),
            "suggestions": opt.get("suggestions", []),
            "highlights": opt.get("highlights", []),
            "optimized_resume": opt.get("optimized_resume", ""),
        }, None
    except Exception as e:
        return None, "离线分析过程出错：%s" % e


# ==============================================================================
# LLM 模式生成
# ==============================================================================

LLM_SYSTEM_PROMPT = """你是一位顶级简历优化顾问与资深招聘专家，曾帮助500+求职者拿到一线互联网公司offer。
你精通STAR法则（Situation-Task-Action-Result），擅长分析岗位JD与简历的匹配度，并将平淡的描述改写为有数据支撑的高匹配度简历。

【输出要求 - 极其重要】
1. 你必须且只能输出一个合法的 JSON 对象，禁止输出任何其他文字、解释、Markdown 代码块标记（如 ```json）。
2. JSON 结构必须严格如下：
{
  "match_score": 0到100的整数（综合匹配度评分）,
  "score_level": "匹配等级描述，如 高度匹配(A) / 较好匹配(B) / 一般匹配(C) / 部分匹配(D) / 匹配度较低(E)",
  "job_title": "JD中的职位名称",
  "candidate_name": "候选人姓名",
  "dimensions": [
    {"name": "技能匹配", "score": 整数, "max": 30, "detail": "一句话说明"},
    {"name": "经验匹配", "score": 整数, "max": 30, "detail": "一句话说明"},
    {"name": "关键词覆盖", "score": 整数, "max": 20, "detail": "一句话说明"},
    {"name": "行业匹配", "score": 整数, "max": 10, "detail": "一句话说明"},
    {"name": "简历质量", "score": 整数, "max": 10, "detail": "一句话说明"}
  ],
  "matched_skills": ["简历已覆盖的JD关键技能", "..."],
  "missing_skills": ["JD要求但简历缺失的关键技能", "..."],
  "suggestions": [
    {"category": "建议分类", "priority": "高/中/低", "issue": "存在的问题", "action": "具体优化动作（含改前→改后示例更佳）", "impact": "带来的效果"},
    {"category": "...", "priority": "...", "issue": "...", "action": "...", "impact": "..."},
    {"category": "...", "priority": "...", "issue": "...", "action": "...", "impact": "..."}
  ],
  "highlights": ["2-4条核心结论摘要"],
  "optimized_resume": "优化后的完整简历全文（Markdown格式，含个人信息/个人亮点/工作经历/项目经验/技能清单）"
}
3. dimensions 五项的 score 之和应等于 match_score（允许±2误差）。
4. 优化规则：将JD高权重关键词自然融入简历描述；"负责/参与/协助"等模糊动词改为"主导/搭建/推动/实现"；补充量化数据（合理估算处标注[请核实]）；不虚构公司、学校、职位。
5. suggestions 给3-6条，按优先级排序。"""

LLM_USER_PROMPT = """请分析以下岗位JD与候选人简历的匹配度，并输出优化建议与优化后简历。

【岗位JD】
%s

【候选人简历】
%s

请严格按 system 中定义的 JSON 结构输出，只输出 JSON 本身。"""


def extract_json(text):
    """从模型输出中提取 JSON 对象（容忍 Markdown 代码块包裹）"""
    if not text:
        return None
    t = text.strip()
    # 去掉 markdown 代码块标记
    if t.startswith("```"):
        lines = t.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        t = "\n".join(lines).strip()
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(t[start:end + 1])
    except Exception:
        return None


def normalize_llm_result(obj):
    """校验并补齐 LLM 返回的字段，保证前端结构稳定"""
    def as_int(v, default=0):
        try:
            return int(float(v))
        except Exception:
            return default

    result = {
        "match_score": max(0, min(100, as_int(obj.get("match_score")))),
        "score_level": str(obj.get("score_level", "")),
        "job_title": str(obj.get("job_title", "")),
        "candidate_name": str(obj.get("candidate_name", "")),
        "dimensions": [],
        "matched_skills": [str(s) for s in obj.get("matched_skills", []) if s],
        "missing_skills": [str(s) for s in obj.get("missing_skills", []) if s],
        "suggestions": [],
        "highlights": [str(h) for h in obj.get("highlights", []) if h],
        "optimized_resume": str(obj.get("optimized_resume", "")),
    }
    for d in obj.get("dimensions", [])[:6]:
        if isinstance(d, dict) and d.get("name"):
            result["dimensions"].append({
                "name": str(d.get("name")),
                "score": as_int(d.get("score")),
                "max": max(1, as_int(d.get("max"), 20)),
                "detail": str(d.get("detail", "")),
            })
    for s in obj.get("suggestions", [])[:8]:
        if isinstance(s, dict):
            result["suggestions"].append({
                "category": str(s.get("category", "优化建议")),
                "priority": str(s.get("priority", "中")),
                "issue": str(s.get("issue", "")),
                "action": str(s.get("action", "")),
                "impact": str(s.get("impact", "")),
            })
    if not result["dimensions"] or not result["optimized_resume"]:
        return None
    return result


def llm_generate(jd_text, resume_text):
    """
    LLM 模式：调用模型生成分析结果。
    JSON 解析失败重试一次；仍失败则降级离线模式。
    返回 (result_dict, source, note)
    """
    user_prompt = LLM_USER_PROMPT % (jd_text, resume_text)

    ok, content = call_llm(LLM_SYSTEM_PROMPT, user_prompt, max_tokens=6000)
    if not ok:
        # LLM 调用本身失败 → 降级离线
        result, err = offline_generate(jd_text, resume_text)
        if result is None:
            return None, "offline", "LLM 调用失败（%s），离线引擎也不可用：%s" % (content, err)
        return result, "offline", "LLM 调用失败（%s），已自动降级为离线规则引擎模式" % content

    obj = extract_json(content)
    result = normalize_llm_result(obj) if obj else None

    if result is None:
        # 重试一次：明确要求只输出 JSON
        retry_prompt = (user_prompt +
                        "\n\n【重要】你上一次的输出不是合法JSON。请重新生成，"
                        "只输出一个以 { 开头、以 } 结尾的合法JSON对象，"
                        "不要包含任何其他文字或Markdown标记。")
        ok2, content2 = call_llm(LLM_SYSTEM_PROMPT, retry_prompt, max_tokens=6000)
        if ok2:
            obj2 = extract_json(content2)
            result = normalize_llm_result(obj2) if obj2 else None

    if result is None:
        # 两次都失败 → 降级离线
        fb, err = offline_generate(jd_text, resume_text)
        if fb is None:
            return None, "offline", "LLM 输出解析失败，离线引擎也不可用：%s" % err
        return fb, "offline", "LLM 输出未通过JSON校验（已重试1次），已自动降级为离线规则引擎模式"

    return result, "llm", ""


# ==============================================================================
# 厂商自动识别
# ==============================================================================

def detect_provider(api_key):
    """
    自动识别 API Key 所属厂商：
    1. 智谱 Key 中间含 '.'，优先试智谱
    2. 并发请求各厂商 GET /models，返回200即命中
    """
    candidates = list(PROVIDERS)
    # Key 格式预判：智谱优先
    if "." in api_key:
        candidates.sort(key=lambda p: 0 if p["name"] == "智谱GLM" else 1)

    hit = {}

    def probe(p):
        try:
            status, data = http_request(
                p["base_url"] + "/models",
                method="GET",
                headers={"Authorization": "Bearer " + api_key},
                timeout=6,
            )
            if status == 200 and isinstance(data, dict):
                models = []
                for m in data.get("data", [])[:30]:
                    if isinstance(m, dict) and m.get("id"):
                        models.append(m["id"])
                hit["provider"] = p
                hit["models"] = models
        except Exception:
            pass

    threads = [threading.Thread(target=probe, args=(p,)) for p in candidates]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=8)

    if "provider" in hit:
        p = hit["provider"]
        return True, {
            "provider": p["name"],
            "base_url": p["base_url"],
            "models": hit["models"],
        }
    return False, "未能识别该 Key 所属厂商（所有厂商探测均失败），可在高级设置里手动填写接口地址"


# ==============================================================================
# 请求处理器
# ==============================================================================

class Handler(BaseHTTPRequestHandler):
    server_version = "ResumeAgentWeb/1.0"

    def log_message(self, fmt, *args):
        sys.stdout.write("[web] " + fmt % args + "\n")

    # ---------- 工具 ----------
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, msg, status=200):
        self._send_json({"ok": False, "error": msg}, status=status)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # ---------- GET ----------
    def do_GET(self):
        try:
            path = self.path.split("?")[0]
            if path == "/" or path == "/index.html":
                self._serve_index()
            elif path == "/api/status":
                self._api_status()
            elif path == "/api/config":
                self._api_get_config()
            else:
                self._send_error("接口不存在：%s" % path, status=404)
        except Exception as e:
            self._send_error("服务器内部错误：%s" % e, status=500)

    def _serve_index(self):
        index_path = os.path.join(BASE_DIR, "index.html")
        if not os.path.exists(index_path):
            self._send_error("index.html 不存在", status=404)
            return
        with open(index_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _api_status(self):
        cfg = load_config()
        has_key = bool(cfg.get("api_key"))
        self._send_json({
            "ok": True,
            "has_key": has_key,
            "provider": cfg.get("provider", "") if has_key else "",
            "model": cfg.get("model", "") if has_key else "",
            "mode": "llm" if has_key else "offline",
        })

    def _api_get_config(self):
        cfg = load_config()
        self._send_json({
            "ok": True,
            "api_key": mask_key(cfg.get("api_key", "")),
            "provider": cfg.get("provider", ""),
            "base_url": cfg.get("base_url", ""),
            "model": cfg.get("model", ""),
        })

    # ---------- POST ----------
    def do_POST(self):
        try:
            path = self.path.split("?")[0]
            if path == "/api/config":
                self._api_post_config()
            elif path == "/api/detect":
                self._api_detect()
            elif path == "/api/test":
                self._api_test()
            elif path == "/api/generate":
                self._api_generate()
            else:
                self._send_error("接口不存在：%s" % path, status=404)
        except Exception as e:
            self._send_error("服务器内部错误：%s" % e, status=500)

    def _api_post_config(self):
        body = self._read_body()
        action = body.get("action", "")
        if action == "clear":
            if os.path.exists(CONFIG_PATH):
                try:
                    os.remove(CONFIG_PATH)
                except Exception:
                    pass
            self._send_json({"ok": True, "message": "配置已清除，已切换为离线规则引擎模式"})
            return

        api_key = str(body.get("api_key", "")).strip()
        provider = str(body.get("provider", "")).strip()
        base_url = str(body.get("base_url", "")).strip()
        model = str(body.get("model", "")).strip()

        if not api_key:
            self._send_error("api_key 不能为空（如需清除配置请使用清除按钮）")
            return

        cfg = load_config()
        cfg["api_key"] = api_key
        if provider:
            cfg["provider"] = provider
        if base_url:
            cfg["base_url"] = base_url.rstrip("/")
        if model:
            cfg["model"] = model
        save_config(cfg)
        self._send_json({
            "ok": True,
            "message": "配置已保存",
            "api_key": mask_key(api_key),
            "provider": cfg.get("provider", ""),
            "model": cfg.get("model", ""),
        })

    def _api_detect(self):
        body = self._read_body()
        api_key = str(body.get("api_key", "")).strip()
        if not api_key:
            self._send_error("请先输入 API Key")
            return
        ok, data = detect_provider(api_key)
        if ok:
            self._send_json({
                "ok": True,
                "provider": data["provider"],
                "base_url": data["base_url"],
                "models": data["models"],
            })
        else:
            self._send_error(data)

    def _api_test(self):
        cfg = load_config()
        if not cfg.get("api_key") or not cfg.get("base_url") or not cfg.get("model"):
            self._send_error("尚未完成配置（需要 api_key / base_url / model），请先在设置中保存")
            return
        t0 = time.time()
        ok, content = call_llm(
            "你是一个连通性测试助手。",
            "请只回复两个字：正常",
            max_tokens=300,  # 思考型模型的think块也占token，给足空间
        )
        latency = int((time.time() - t0) * 1000)
        if ok:
            self._send_json({
                "ok": True,
                "latency_ms": latency,
                "reply": content.strip()[:50],
            })
        else:
            self._send_error(content)

    def _api_generate(self):
        body = self._read_body()
        jd_text = str(body.get("jd_text", "")).strip()
        resume_text = str(body.get("resume_text", "")).strip()
        if not jd_text:
            self._send_error("请填写职位描述（JD）")
            return
        if not resume_text:
            self._send_error("请填写简历内容")
            return
        if len(jd_text) > 20000 or len(resume_text) > 20000:
            self._send_error("输入内容过长（单边上限20000字）")
            return

        cfg = load_config()
        if cfg.get("api_key") and cfg.get("base_url") and cfg.get("model"):
            result, source, note = llm_generate(jd_text, resume_text)
        else:
            result, err = offline_generate(jd_text, resume_text)
            source, note = ("offline", "") if result else ("offline", err or "")

        if result is None:
            self._send_error(note or "分析失败，请稍后重试")
            return

        resp = {"ok": True, "source": source}
        if note:
            resp["note"] = note
        resp.update(result)
        self._send_json(resp)


# ==============================================================================
# 启动
# ==============================================================================

def find_free_port(start=8001, end=8020):
    import socket
    for port in range(start, end + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return None


def main():
    port = find_free_port()
    if port is None:
        print("[错误] 8001~8020 端口均被占用，请释放端口后重试")
        return 1

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % port

    print("=" * 56)
    print("  AI简历优化Agent · 本地网站版")
    print("=" * 56)
    print("  访问地址: %s" % url)
    print("  浏览器将自动打开；如未打开请手动访问上方地址")
    print("  按 Ctrl+C 停止服务")
    print("=" * 56)

    def open_browser():
        open_app_window(url)

    threading.Timer(1.0, open_browser).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止服务")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
