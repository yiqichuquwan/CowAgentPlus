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
> #### 本 fork 相对上游的主要改动
>
> | 改动 | 说明 |
> | :--- | :--- |
> | 🌐 **Web 控制台 → 可安装 PWA**（能力保留） | 新增 [Web App Manifest](https://developer.mozilla.org/docs/Web/Manifest)（中/英双语）、Service Worker、maskable 图标与全套 iOS 启动图。`PwaFileHandler` 从控制台根路径提供 `/manifest*.webmanifest` 与 `/sw.js`，前端注册 SW 但**不再拦截 `beforeinstallprompt`**——浏览器地址栏 / 「安装应用」菜单的原生安装 UI 可直接使用。Web UI 内不再提供自定义安装按钮。 |
> | ⚡ **流式回复零影响** | Service Worker 仅缓存静态外壳（HTML / CSS / JS / 图标 / manifest），所有实时通道（SSE `/stream`、`/poll`、`/api/*`、文件上传）一律直通网络——流式回复、轮询、上传行为与上游完全一致。 |
> | 🔄 **接回上游一键更新** | 已同步上游 `c28fff5` + `43edb84` + `7236846`：Web 控制台版本号旁的下拉菜单提供「检查更新 / 立即更新 / 版本说明」，由 `cli/update_service.py` 驱动——自动 git pull → 重启。 |
> | 🐛 **Web 智能体管理面板：切换时技能面板刷新** | 修复 bug：在「能力」tab 切换左侧其他智能体时，勾选状态停留在上一个智能体（顶栏头像/名字已更新，但可见的技能面板未刷新）。`openAgentDetail()` 现在会按当前激活 tab 主动重渲染对应面板。 |
> | 🧹 **仓库卫生** | `.gitignore` 新增 `config.json.bak.*`：`app.py` 启动时检测到配置变更会自动写一份带 epoch 后缀的 `.bak`，属于运行期产物，不入版本库。 |
>
> 其余代码与上游同步；本 fork **只在 Web 控制台前端与仓库卫生层面**做增量改进，不修改 Agent 核心 / Model / Channel / Memory / Knowledge 等逻辑。
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