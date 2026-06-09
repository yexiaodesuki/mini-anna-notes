测试目标

请实现一个本地运行的 Anna App：Mini Notes with LLM Summary。

本测试主要考察：
- 对 Anna App 本地开发模型的理解
- 对 Anna Host API、storage / APS KV 语义、Executa Tool、JSON-RPC over stdio、sampling 的理解
- 工程化前端项目能力
- 本地可复现测试能力
- Executa Tool 二进制打包与 GitHub Actions 发布能力

注意：
- 不需要接入真实 Anna 账号。
- 不需要 `anna-app login`。
- 不需要真实 LLM API key。
- 不需要云端数据库。
- 必须使用 Anna 本地开发模型：`anna-app dev` 启动本地 harness，UI bundle 通过 Anna App Runtime 调用 Host API。

---
开发文档

请先阅读 Anna 开发者文档和示例仓库：

- 示例仓库：https://github.com/whtcjdtc2007/anna-executa-examples
- 开发文档：https://staging.anna.partners/developers

你至少需要理解：
- Anna App 是什么。
- Executa Tool 是什么。
- Anna App 如何通过 Host API 与本地 harness 交互。
- Executa Tool 如何通过 stdio 与 Anna 通信。
- 本地开发、测试和打包发布的大致流程。

---
任务描述

请实现一个 Mini Notes App。

用户可以创建、查看、删除笔记。笔记必须通过 Anna App 的 storage Host API 保存，不能绕过 Anna 平台模型。用户点击 Summarize 后，前端必须通过 Anna Host API 调用本地 Executa Tool；该 Tool 必须使用 sampling 向 host LLM 请求总结，并把总结结果返回给前端展示。

核心链路必须是：

```text
Anna App iframe
  -> AnnaAppRuntime.connect()
  -> anna.storage.* 保存 / 读取 notes
  -> anna.tools.invoke(...)
  -> 本地 Executa Tool invoke
  -> reverse JSON-RPC sampling/createMessage
  -> host LLM 或本地 mock sampling fixture
  -> summary 返回 UI
```

---
功能要求

1. 创建笔记

用户可以输入一段简短文字并保存。

要求：
- 空输入不能保存。
- 保存后输入框应清空。
- 笔记应包含内容和添加顺序。

示例：
- 明天跟客户 follow up
- 修复登录 bug
- Workshop 内容想法

2. 查看笔记列表

页面应展示已经保存的笔记。

至少包含：
- 笔记内容
- 添加顺序

可选：
- 时间戳
- 空状态
- 错误状态

3. 删除笔记

用户可以删除一条笔记。

删除后：
- 列表应立即更新。
- 应通过 `anna.storage.*` 更新存储中的 notes。

4. Anna storage / APS KV 持久化

笔记必须通过 Anna App 的 storage Host API 保存。具体 API 用法请自行阅读官方文档和示例仓库。

要求：
- 不能只使用 React/Vue/Svelte state。
- 不能只使用 `localStorage` / IndexedDB / 文件系统。
- 创建、查看、删除流程必须严格调用 `anna.storage.get` / `anna.storage.set` 或等价 storage Host API。
- 本地测试不需要真实 Anna 账号，直接使用 `anna-app dev` 默认的 legacy in-memory runtime_state。
- 本地 legacy runtime_state 只用于无 login 的 harness 调试；不要求刷新外层 `anna-app dev` dashboard 或重启 dev 后 notes 仍保留。

5. LLM 总结

页面提供 Summarize 按钮。

点击后：
- 前端从 Anna storage Host API 中读取当前 notes，或使用已和 storage 同步的当前 notes。
- 前端通过 `anna.tools.invoke(...)` 调用本地 Executa Tool。
- Executa Tool 的 `invoke` 处理 summarize 请求。
- Tool 内部必须发起 reverse JSON-RPC `sampling/createMessage`。
- summary 必须来自 sampling 返回结果，而不是前端或 Tool 的固定规则拼接。
- UI 展示 summary。

不接受：
- 前端直接调用 `anna.llm.complete` 完成总结。
- 前端直接 fetch 自建 HTTP API。
- 前端本地规则生成 summary。
- Tool 本地规则生成 summary 后假装是 LLM。

---
技术要求

1. Anna App manifest

必须包含 `manifest.json`，并合理声明：
- `schema`
- `required_executas`
- `permissions`
- `ui.bundle`
- `ui.views`
- `ui.host_api.storage`
- `ui.host_api.tools`
- 本地开发所需 `dev` 配置

`required_executas`、`ui.host_api.tools`、前端调用常量、Executa manifest / `describe` 返回的 tool identity 必须保持一致。

2. 工程化前端

前端必须是工程化项目。

要求：
- 需要有源码目录，例如 `src/`。
- UI、Anna runtime 连接、storage 访问、tools 调用等逻辑应有基本拆分。
- 需要有包管理配置和构建脚本。
- 需要能通过 `npm run build` / `pnpm build` / `yarn build` 或等价命令生成 Anna App 可加载的静态 bundle。
- `manifest.json` 的 `ui.bundle.entry` 应指向构建后的 bundle 入口。

不接受：
- 只提交一个手写 SPA HTML 文件。
- 所有 JS/CSS/业务逻辑全部塞在一个 HTML 文件里。
- 只能作为普通 Web App 运行，不能通过 `anna-app dev` 运行。

3. Executa Tool

必须实现一个本地 Executa Tool。

要求：
- 使用 JSON-RPC 2.0 over stdio。
- stdin 每行读取一个 JSON-RPC 请求。
- stdout 只能输出 JSON-RPC 响应，不得输出日志、banner、debug 文本。
- 日志必须输出到 stderr。
- 响应后必须 flush。
- 进程必须持续读取 stdin 直到 EOF，不能处理一次请求就退出。

至少实现：
- `initialize`：完成 v2 capability negotiation，并声明 sampling capability。
- `describe`：返回裸 manifest。
- `invoke`：处理 summarize tool。
- `health`：可选但建议实现。
- `shutdown`：可选但建议实现。

`describe` 返回的 manifest 至少包含：
- `name`
- `display_name`
- `version`
- `description`
- `host_capabilities: ["llm.sample"]`
- `tools[]`
- `runtime`

`tools[]` 中 summarize 的参数 schema 应使用 Anna Executa 协议的 `parameters[]` 形态，不要只写 MCP 风格 `input_schema`。

4. Sampling

Executa Tool 必须通过 reverse JSON-RPC 发起 `sampling/createMessage`。

要求：
- `initialize` 成功协商 protocol v2 时，Tool 需要声明 `client_capabilities.sampling = {}`。
- Tool manifest 需要声明 `host_capabilities: ["llm.sample"]`。
- `sampling/createMessage` 请求应包含当前 notes 的内容和合理 prompt。
- 应在 metadata 中携带当前 `invoke_id` 或等价关联信息，便于审计和调试。
- Tool 需要正确处理 host 对 reverse RPC 的 response；同一个 stdin reader 会收到 agent 发来的请求，也会收到 host 对 sampling 请求的响应。

5. 本地测试与 mock

测试不需要 `anna-app login`。

要求：
- App UI harness 测试必须可以使用 `anna-app dev --no-llm` 启动；可以用 npm / pnpm / yarn script 封装该命令。
- UI harness 只需要验证 App、storage Host API、`anna.tools.invoke` wiring，不要求在这一条路径里完成后端 sampling mock。
- 在 `--no-llm` 模式下点击 Summarize 时，前端仍应正常调用 `anna.tools.invoke(...)`；由于 harness 禁用了 LLM/sampling，预期会得到类似 `[-32603] harness started with --no-llm` 的错误。README 应说明这是 App 调试路径的预期结果，不代表后端 Tool sampling 失败。
- 后端 Executa Tool 的 sampling 必须通过 `anna-app executa dev --mock-sampling <fixture.jsonl>` 单独测试。
- 仓库中必须包含 `--mock-sampling` 使用的 fixture。
- README 必须说明如何确认 `sampling/createMessage` 被 Tool 发起过。
- 如果提供 fixture recording / harness log / 手动协议测试脚本，应说明如何读取证据。

注意：
- 不应在 UI harness 中用 mock fixture 伪造最终 summary 来替代后端 sampling 测试。
- 本题重点是本地可复现，不要求真实模型效果。

6. Executa binary 打包

需要提供 Executa Tool 的打包脚本。

要求：
- 不限制实现语言。
- 但所选技术栈必须能完成三平台二进制打包。
- 不接受“源码 + 解释器运行”作为发布产物。
- 打包脚本应能识别本机架构，构建当前机器可运行的二进制 archive。
- 最终 archive 必须符合 Anna binary distribution 文档要求。
- 具体 archive 结构、manifest 字段、entrypoint、权限和平台 key 规则，请按照官方 Executa binary distribution 文档实现：https://staging.anna.partners/developers/tools/executa-binary

至少支持这些平台 key：
- `darwin-arm64`
- `darwin-x86_64`
- `windows-x86_64`

最终 release asset 格式：
- macOS：`.tar.gz`
- Windows：`.zip`

7. GitHub Actions 发布

必须提供 GitHub Actions workflow。

要求：
- 文件位于 `.github/workflows/`。
- 至少支持 `workflow_dispatch` 或 tag/release 触发。
- 一次发布必须构建并上传三个平台的 release assets：
  - `*-darwin-arm64.tar.gz`
  - `*-darwin-x86_64.tar.gz`
  - `*-windows-x86_64.zip`
- 上传目标必须是 GitHub Release assets。
- Workflow artifacts 可以作为辅助产物，但不能替代 Release assets。
- Workflow 中应包含基本 smoke test，例如对构建出的二进制发送 `describe` JSON-RPC 并验证响应。

8. README

README 必须包含：
- 项目结构说明。
- 安装依赖说明。
- 如何构建前端 bundle。
- 如何运行 `anna-app validate --strict`。
- 如何用 `anna-app dev --no-llm` 启动并测试 UI harness。
- 为什么在 `--no-llm` 下点击 Summarize 预期会得到 `[-32603] harness started with --no-llm` 或等价错误。
- 如何用 `anna-app executa dev --mock-sampling` 单独测试后端 Executa sampling。
- 如何手动测试 Executa JSON-RPC，至少覆盖 `initialize`、`describe`、`invoke`。
- 如何确认 notes 存储走的是 `anna.storage.*`。
- 如何确认 summary 走的是 `anna.tools.invoke -> Executa -> sampling/createMessage`。
- 如何执行本机二进制打包脚本。
- GitHub Actions release workflow 的触发方式和预期 release assets。
- 简短解释 manifest、bundle、executas、Anna storage / APS KV、sampling、binary archive 的关系。

---
最终交付物

请提交一个 GitHub 仓库链接。

仓库必须包含：
- 完整源码。
- 工程化前端项目。
- Anna App `manifest.json`。
- 本地 Executa Tool 源码。
- mock sampling fixture。
- 本地测试脚本或说明。
- Executa 二进制打包脚本。
- GitHub Actions release workflow。
- README.md。

---
验收标准

审阅者会尽量按以下方式验收：

1. 安装依赖。
2. 构建前端 bundle。
3. 运行 `anna-app validate --strict`。
4. 运行 `anna-app dev --no-llm`。
5. 在 UI 中创建 notes、删除 note，并通过代码、RPC log、recording 或其他证据确认读写走的是 `anna.storage.get` / `anna.storage.set`。
6. 点击 Summarize，确认 UI 会通过 `anna.tools.invoke` 触发本地 tool 路由；在 `--no-llm` 下预期会得到 `[-32603] harness started with --no-llm` 或等价错误。
7. 运行 `anna-app executa dev --mock-sampling <fixture.jsonl>` 单独验证后端 Tool 的 sampling 路径。
8. 检查日志、fixture、recording 或手动协议测试，确认后端 Tool 发起过 `sampling/createMessage`。
9. 手动测试 Executa JSON-RPC 的 `initialize`、`describe`、`invoke`。
10. 执行本机二进制打包脚本，检查 archive 结构和 archive root `manifest.json`。
11. 审阅 GitHub Actions workflow，确认它能一次发布三平台 GitHub Release assets。

---
明确不要求

- 不要求真实 Anna 账号。
- 不要求 `anna-app login`。
- 不要求真实 LLM API key。
- 不要求真实云端 APS。
- 不要求本地 legacy in-memory runtime_state 在刷新外层 harness dashboard 或重启 dev 后保留。
- 不要求线上发布 Anna App。
- 不要求代码签名、公证或 Windows Authenticode。
- 不要求复杂 UI 美化。
- 不要求编辑、搜索、标签、多笔记本、富文本、附件、协同。

---
重点提醒

本题不是普通 Web App 题。

如果实现只是在浏览器里保存 notes，并直接调用本地 HTTP 服务或本地函数生成 summary，即使 UI 可用，也不符合要求。

必须体现 Anna App 的平台模型：
- App iframe 通过 Anna Runtime 调 Host API。
- Notes 存储走 Anna storage Host API；本地无 login 时使用 legacy in-memory runtime_state 验证 `get` / `set` 调用。
- Summary 调用走 Executa Tool。
- Executa Tool 通过 sampling 借用 host LLM。
- UI harness 通过 `anna-app dev --no-llm` 本地调试；后端 sampling 通过 `anna-app executa dev --mock-sampling` 单独验证。
- Executa Tool 有可发布的三平台二进制产物。
