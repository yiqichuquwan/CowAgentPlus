<p align="center"><img src="https://github.com/user-attachments/assets/eca9a9ec-8534-4615-9e0f-96c5ac1d10a3" alt="CowAgent" width="420" /></p>

<p align="center">
  <a href="https://github.com/zhayujie/CowAgent/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
</p>

> [!IMPORTANT]
>
> ### 🐮 This is a personal fork: **CowAgentPlus**
>
> 本仓库是 [`zhayujie/CowAgent`](https://github.com/zhayujie/CowAgent) 的个人 fork —— **CowAgentPlus**。
> 上游：<https://github.com/zhayujie/CowAgent> · 本仓库：<https://github.com/yiqichuquwan/CowAgentPlus>
>
> #### Fork 提交历史与上游对照（按时间顺序）
>
> 下表列出 `dev` 分支相对于 `upstream/master` HEAD (`5fd138cf`) 的全部 fork 私有提交，按提交时间从旧到新排列。**「已丢弃」** 表示在 rebase / 同步时可放心 `git revert` 或在 rebase 时丢弃该提交；**「仍需保留」** 表示上游尚未覆盖该改动，丢弃会回归问题。
>
> | # | 提交 | 改动 | 上游状态（截至 `upstream/master` @ `5fd138cf`） |
> | :-: | --- | --- | --- |
> | 1 | `9995d8dc` | `.gitignore` 新增 `config.json.bak.*` | **仍需保留**——upstream `.gitignore` 只忽略整个 `config.json`，未匹配 `.bak.*` 后缀，运行期备份仍会被 `git status` 列出 |
> | 2 | `7f6e44b0` | Web 控制台改造为可安装 PWA（manifest + Service Worker + 启动图） | **仍需保留**——upstream `channel/web/static/` 下无任何 manifest / sw.js，PWA 设施整体缺失 |
> | 3 | `fde983ad` | README 新增 fork 公告 | **不适用**——fork 元信息，不在上游比较范围内 |
> | 4 | `8eb4f82d` | README 同步上游后更新 fork 公告 | **不适用** |
> | 5 | `19a06bde` | README 精简为只展示 fork 改造信息 | **不适用** |
> | 6 | `7659a95d` | feishu 定时任务推送统一使用飞书卡片格式（`build_text_delivery(force_card=...)`） | **仍需保留**——upstream `feishu_static_card.py::build_text_delivery` 无 `force_card` 参数，定时任务仍走原生 text |
> | 7 | `3476e2ea` | 控制台输入草稿按 (Agent, 会话) 保存 + 用户消息气泡加复制按钮 | **仍需保留**——upstream `console.js` 无 `DRAFT_KEY_PREFIX` / `activeDraftStorageKey` / `saveDraft`，也未给用户消息气泡挂复制按钮 |
> | 8 | `87dfbed8` | 取消跟踪 `.preview_secret`（HMAC 密钥），轮换本机旧值 | **仍需保留**——upstream `.gitignore` 已含 `.preview_secret`，但**文件本身仍入库**（`git ls-tree upstream/master .preview_secret` 命中），本 fork 才真正 `git rm --cached` |
> | 9 | `bc582f73` | 自定义 embedding provider 允许无 api_key（keyless local 服务兼容） | **仍需保留**——upstream `agent/memory/embedding/factory.py` 在 `if not api_key:` 分支直接 `return None` 并报 "API key is missing"，未对 `custom:` 前缀做特例 |
> | 10 | `6863a1b0` | Web 侧边栏浅色主题样式（`.sidebar-item.active` 双套色） | **仍需保留**——upstream `.sidebar-item.active` 仍是深色硬编码（`rgba(255,255,255,0.08)` + `#FFFFFF`），浅色模式下左黑右白 |
> | 11 | `85603579` | 移除 sidebar 自定义 PWA 安装按钮 | **不适用**——依赖本 fork 的 PWA 改造（提交 2），upstream 无此按钮 |
> | 12 | `21b29a24` | merge: pull upstream multi-agent features into dev | **同步点**——纯 merge，无独立代码改动；保留是为了不在未来 rebase 时误以为是私有提交 |
> | 13 | `e20a9297` | 切换智能体时重绘当前可见的技能面板（`openAgentDetail` 检测激活 tab） | **仍需保留**——upstream `console.js::openAgentDetail` 仍只重渲染 profile + 核心文件，可见技能面板不刷新 |
>
> > **如何复用本表**：上游 release 后执行 `git fetch upstream && git log --oneline upstream/master..HEAD`，把不再出现的提交标为「已丢弃」并 `git revert`；其余保持。每次上游同步后再核一次即可。
>
> 其余代码与上游同步；本 fork 以 **Web 控制台前端 + 仓库卫生**为主，少量触及 Channel（feishu，见 #6）与 Memory（embedding，见 #9）层；不修改 Agent 核心 / Model / Knowledge 主流程。
>
> 同步上游：在 `dev` 分支执行 `git fetch upstream && git merge upstream/master` 即可（首次合并需手动解决 `chat.html` sidebar footer 区的位置冲突；之后的合并通常自动）。

<br/>

## 关于本仓库

本仓库是 [`zhayujie/CowAgent`](https://github.com/zhayujie/CowAgent) 的个人 fork，本 README 仅承载 fork 相对上游的改动说明。

完整的产品介绍、安装指南、模型 / 通道 / 技能 / 记忆 / 知识库 / 多智能体 / 架构 / 更新日志等内容，请参阅上游 README：

- 英文：<https://github.com/zhayujie/CowAgent/blob/master/README.md>
- 简体中文：<https://github.com/zhayujie/CowAgent/blob/master/docs/zh/README.md>
- 繁體中文：<https://github.com/zhayujie/CowAgent/blob/master/docs/zh/README-Hant.md>
- 日本語：<https://github.com/zhayujie/CowAgent/blob/master/docs/ja/README.md>