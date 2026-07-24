# AI 简历优化 Agent

输入 JD（职位描述）和你的简历，2 分钟输出针对该岗位的匹配度分析 + 优化建议。

## 第一次使用（Clone 之后照做）

按下面 4 步走，2 分钟跑起来：

### 第 1 步：确认有 Python

打开命令行（Windows 按 `Win+R` 输入 `cmd`，Mac 打开"终端"），输入：

```bash
python --version
```

- 显示 `Python 3.7.x` 或更高 → 跳过第 2 步，直接第 3 步
- 提示"不是内部命令" → [去 python.org 下载](https://www.python.org/downloads/) ，**安装时务必勾选 `Add Python to PATH`**

### 第 2 步：把项目下到本地

点 GitHub 仓库页右上角绿色 `Code` 按钮 → `Download ZIP`，解压到你想要的目录。

### 第 3 步：双击启动

| 系统 | 操作 |
|------|------|
| Windows | 双击 `webapp/start.cmd` |
| Mac / Linux | 终端进入 `webapp/` 目录执行 `python3 start.py` |

启动成功会**自动打开浏览器**到 `http://127.0.0.1:8001/`（端口被占会自动换到 8001-8020 之间的空闲端口，看终端提示）。

### 第 4 步：选模式

- **不填 Key**：默认走**离线模式**，内置规则引擎，2 分钟拿到完整分析结果
- **填 Key 走 AI 模式**（推荐，效果更好）：点页面右上角 ⚙️ 设置 → 粘贴你的 API Key → 点「自动识别并保存」→ 点「测试连接」成功即可

> 支持 DeepSeek / Moonshot Kimi / 智谱 GLM / 通义千问 / MiniMax / OpenAI，**自动识别厂商**，不用手动选。
> Key 只保存在你本地的 `webapp/config.json`，**不会上传任何地方**（这个文件已被 `.gitignore` 排除）。

## 5 秒上手

### Windows 用户（推荐）

双击 `webapp/start.cmd`

或直接双击 `webapp/start.py`（前提：.py 文件已关联 Python）

### Mac / Linux 用户

```bash
cd webapp
python3 start.py
```

服务起来后浏览器会自动打开 `http://127.0.0.1:8001/`。

### 命令行版（不开网页）

```bash
cd code
python3 resume_agent.py
```

直接输出 JSON 报告到终端。

## 三种使用模式

| 模式 | 触发条件 | 效果 |
|---|---|---|
| **LLM 模式** | 网页设置里填了 API Key | 走真模型，分析更精准、文案更自然 |
| **离线模式** | 没填 Key / Key 失效 | 自动降级到内置规则引擎，结果是模板化的但完整可用 |
| **命令行模式** | 直接跑 `resume_agent.py` | 离线规则引擎 |

### 配 API Key（可选）

支持的厂商：
- DeepSeek
- Moonshot Kimi
- 智谱 GLM
- 通义千问
- MiniMax（含国际版）
- OpenAI

填 Key 时**自动识别厂商**，不用手动选。

## 文件结构

```
项目A-简历优化Agent/
├── README.md
├── 使用说明.md              ← 详细使用文档
├── 项目设计方案.md          ← 产品设计
├── 核心Prompt设计.md        ← Prompt 工程
├── 工作流设计.md            ← 工作流图
├── 演示案例.md              ← 真实案例
├── webapp/
│   ├── start.py             ← 一键启动（推荐）
│   ├── start.cmd            ← 一键启动（Windows）
│   ├── stop.py              ← 停止服务
│   ├── stop.cmd
│   ├── server.py            ← 后端服务
│   ├── index.html           ← 前端页面
│   ├── 启动网站.bat         ← 旧版启动入口（保留）
│   └── test_webapp.log      ← 历史测试日志
└── code/
    ├── resume_agent.py      ← 智能体核心（命令行版）
    └── test_output.log      ← 历史测试日志
```

## 依赖

- **仅 Python 3.7+ 标准库**（无第三方依赖）
- 任意主流操作系统（Windows / macOS / Linux）

## 验证情况

| 项目 | 状态 |
|---|---|
| 一键启动（start.py） | ✅ 8001 端口 HTTP 200 |
| 命令行运行 | ✅ exit 0，输出 JSON 报告 |
| 网页 API（/api/generate 离线） | ✅ 5 维度 + 4 建议 |
| LLM 模式 | ✅ 自动识别 6 家厂商 Key |

## 常见问题

**Q: 端口 8001 被占？**
A: `server.py` 自动找 8001-8020 空闲端口。看启动后输出的"访问地址"。

**Q: 没配 Key 能用吗？**
A: 能，自动用离线模式，效果是规则模板但完整。

**Q: 配了 Key 还是离线模式？**
A: 网页"设置"里看 Key 是否被识别为有效格式。或看 `server.log`。

**Q: 想换端口范围？**
A: 编辑 `webapp/server.py` 里的 `find_free_port(start=8001, end=8020)`。

## License

MIT

## 关于作者

由李建鹏设计开发 · 作品集主页：https://lijianpeng-arch.github.io/