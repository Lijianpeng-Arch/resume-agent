# AI 简历优化 Agent

输入 JD（职位描述）和你的简历，2 分钟输出针对该岗位的匹配度分析 + 优化建议。

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