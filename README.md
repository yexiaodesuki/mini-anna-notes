# Mini Anna Notes

Mini Anna Notes 是一个基于 Anna App 架构的轻量级本地笔记应用。本项目旨在完成一个本地运行的可以创建笔记，保存笔记且总结的笔记应用。它包含一个纯前端的交互界面，以及一个基于 Python 的本地规则驱动（Rule-based）总结工具，能够自动对输入的笔记内容进行总结。

## 目录结构
```text
mini-anna-notes/
├─ bundle/                      # 前端 UI（用户交互层）
│  ├─ index.html
│  └─ app.js
│
├─ executas/
│  └─ notes-summarizer/        # 本地 Executa Tool（后台逻辑）
│     ├─ tool.py
│     ├─ pyproject.toml
│     └─ uv.lock
│
├─ manifest.json               # Anna App 配置（工具注册 + 权限）
├─ app.json                    # 应用基础元数据
└─ README.md                   # 项目说明文档
```

## 如何安装依赖

1. 安装 Node.js

在终端输入
```bash
winget install OpenJS.NodeJS.LTS
```

2. 安装 uv

在终端输入
```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. 安装anna-app CLI

在终端输入
```bash
  npm i -g @anna-ai/cli
```

4. 启动

这里要运行
```bash
anna-app dev --no-llm
```
不能省略 --no-llm 选项，否则 CLI 会尝试连接远端 LLM 服务，需要 developer PAT（登录态），本地无法直接运行

## 如何手动测试 Executa JSON-RPC

Anna App 的 Executa 遵循 JSON-RPC 2.0 规范，并通过 标准输入/输出 (stdio) 进行通信。tool.py 被设计为从 stdin 读取请求，将结果输出到 stdout，并将日志输出到 stderr 以防止污染通信流。

你可以通过命令行管道（Pipe）输入 JSON 字符串的方式来手动测试它。在 executas/notes-summarizer 目录下打开终端：

测试 describe 方法 (获取工具元数据)
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "describe"}' | python tool.py
```

预期输出：一段包含 name、description 和 input_schema 的 JSON 数据。

测试 invoke 方法 (执行工具逻辑)
```bash
echo '{"jsonrpc": "2.0", "id": 2, "method": "invoke", "params": {"arguments": {"notes": ["修复了登录bug", "下午和客户开会", "写下周的文档"]}}}' | python tool.py --pretty
```

预期输出：result 字段将包含分类统计后的 summary 文本，例如：“当前共有 3 条待处理事项，主要集中在开发、协作 和 内容准备。”

## Bundle / Manifest / Executas 的关系

在 Anna App 生态中，应用分为三个核心部分。各自的作用和关系如下：

### Bundle (前端 UI 层)

位置：bundle/ (包含 index.html, app.js)

作用：它是用户直接看到和交互的界面。在本项目中，它负责渲染UI,执行输入/保存笔记的功能，且调用runtime。

特点：它运行在沙箱环境中，通过 @anna-apps/_sdk (AnnaAppRuntime) 向底层发起调用请求。它不关心底层的工具是用 Python、Node.js 还是 Rust 编写的。

### Executas (本地计算/工具层)

位置：executas/ (包含 notes-summarizer/tool.py)

作用：它是真正在后台执行密集计算、数据处理或 AI 推理的独立进程，实现Executa Tool，支持describe和invoke。

特点：它没有 UI，通过监听标准输入 (stdin) 接收来自 Anna Runtime 转发的 JSON-RPC 请求，处理完毕后通过标准输出 (stdout) 原路返回。本项目中的笔记总结逻辑就运行在这里。

### Manifest (配置与桥梁)

位置：manifest.json

作用：它是整个应用的配置文件，定义了应用结构，注册 executa tool，配置 runtime 权限，描述 UI entry


### Bundle -> Manifest -> Executas -> 笔记总结

用户在 Bundle（前端页面）点击“Summarize”按钮后，app.js 通过 AnnaAppRuntime.connect() 获取的 SDK 调用 anna.tools.invoke() 发起工具请求。

JS SDK 会首先读取 manifest.json，确认当前应用是否拥有调用该 tool_id（Executa Tool）的权限，以及该工具是否已注册。

如果权限校验通过，Anna Runtime 会将前端的调用请求封装成标准 JSON-RPC 请求，并通过本地 stdio 通信发送给 Executa 进程。

Executa（tool.py）作为独立子进程运行，监听 stdin 中的 JSON-RPC 请求，解析 invoke 方法后读取 arguments.notes，执行本地规则计算，生成 summary。

处理完成后，Executa 将结果以 JSON-RPC response 格式写入 stdout 返回给 Anna Runtime。

Anna Runtime 接收到结果后，将 response 解析并回传给前端 JS SDK，anna.tools.invoke() 返回 Promise resolve 的结果对象。

最后，前端 app.js 读取 res.summary 并渲染到页面，实现最终的总结展示。