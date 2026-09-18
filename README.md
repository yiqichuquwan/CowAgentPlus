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
> 下表列出 `dev` 分支相对于 `upstream/master` HEAD (`8f1b19f1`) 的全部 fork 私有提交，按提交时间从旧到新排列。**「已丢弃」** 表示在 rebase / 同步时可放心 `git revert` 或在 rebase 时丢弃该提交；**「仍需保留」** 表示上游尚未覆盖该改动，丢弃会回归问题。
>
> | # | 提交 | 改动 | 上游状态（截至 `upstream/master` @ `8f1b19f1`） |
> | :-: | --- | --- | --- |
> | 1 | `6aa1f77e` | `.gitignore` 加 `config.json.bak.*` + `git rm --cached .preview_secret`（HMAC 密钥），轮换本机旧值 | **仍需保留**——upstream `.gitignore` 只忽略整个 `config.json`，未匹配 `.bak.*` 后缀；upstream `.gitignore` 已含 `.preview_secret`，但**文件本身仍入库**（`git ls-tree upstream/master .preview_secret` 命中），本 fork 才真正 `git rm --cached` |
> | 2 | `cf06f5ae` | README fork 公告 + 改动对照表 | **不适用**——fork 元信息，不在上游比较范围内 |
> | 3 | `126ebc1d` | Web 控制台改 PWA（manifest / sw / 图标 / 启动图）+ `PwaFileHandler` 根路由 + HTTPS cookie（`_is_secure_request`）+ `chat.html` 补回 sidebar/session-panel/team-chat 三个 include | **仍需保留**——upstream `channel/web/static/` 无任何 manifest / sw.js；无 `PwaFileHandler`；无 `_is_secure_request`；`pages.py::RootHandler` 仍用 `seeother('/')`（web_channel.py 拆分 PR #3174 合并时漏删 include，已修） |
> | 4 | `69ed8591` | 控制台输入草稿按 (Agent, 会话) 存 localStorage + 用户消息气泡加复制按钮 + 切换智能体时刷新可见技能面板 | **仍需保留**——upstream `chat/composer-input.js` / `send.js` / `state.js` 等无 `DRAFT_KEY_PREFIX` / `saveDraft` / 复制按钮；`openAgentDetail` 不重绘可见技能面板 |
> | 5 | `a144fc39` | Web 侧边栏浅色主题（`.sidebar-item.active` / `.update-menu` / `.update-menu-item` 双套色） | **仍需保留**——upstream 拆分后的 `templates/layout/sidebar.html` 与 `static/css/sessions.css` 仍硬编码深色，浅色模式下左黑右白 |
> | 6 | `b2ad1621` | Web 发送失败可见化（web.py LogMiddleware 改回 run.log + cheroot pool stats + `postMessage` 15s 超时）+ 飞书 evolution 通知改卡片（`_notify_user` 增 request_id/data 参数） | **仍需保留**——upstream `LogMiddleware.log` 仍 no-op，cheroot pool 饱和时连接在 handler 之前就被拒，server-side 无任何 trace；evolution `_notify_user` 仍走原生 text，长文/Markdown 在飞书 app 渲染差 |
> | 7 | `368d8ca7` | feishu 定时任务推送统一卡片格式（`build_text_delivery(force_card=True)`） | **仍需保留**——upstream `feishu_static_card.py::build_text_delivery` 无 `force_card` 参数，定时任务仍走原生 text |
> | 8 | `a7845cce` | embedding 自定义 provider 允许无 api_key（`custom:` 前缀特例，兼容 keyless 本地服务如 TEI / bge-m3） | **仍需保留**——upstream `agent/memory/embedding/factory.py` 在 `if not api_key:` 分支直接 `return None` 并报 "API key is missing"，未对 `custom:` 前缀做特例 |
> | 9 | `3e398b2c` | `run.sh` 优先 `.venv/bin/python` + `pip_cmd()` 回退到 `uv pip`（避免污染宿主 `~/.local`） | **仍需保留**——upstream `run.sh` 仍装进系统 Python user site，常用 `--break-system-packages`，无 venv 探测 |
> | 10 | `840de1b9` | 修复宿主环境泄漏导致的测试失败（conftest 提前 import requests / `load_config` 还原 cow_lang / `get_conversation_store()` 与 runner 同源 / catalog overlay 隔离 / SSRF 测试 stub `_check_engine_ready` / `conversation_store._ensure_schema` 加 `_schema_present()` 探测）+ 新增 `AGENTS.md` 记录 venv 差异 | **仍需保留**——`conversation_store._ensure_schema` 的 `_schema_present()` 探测与宿主语言/路径/可选依赖隔离修复 upstream 均无 |
>
> > **如何复用本表**：上游 release 后执行 `git fetch upstream && git log --oneline upstream/master..HEAD`，把不再出现的提交标为「已丢弃」并 `git revert`；其余保持。每次上游同步后再核一次即可。
>
> 其余代码与上游同步；本 fork 以 **Web 控制台前端（#3–#6）+ 仓库卫生（#1、#10）**为主，少量触及 Channel（feishu，见 #7）与 Memory（embedding，见 #8）层；不修改 Agent 核心 / Model / Knowledge 主流程。
>
> 同步上游：在 `dev` 分支执行 `git fetch upstream && git merge upstream/master` 即可（首次合并若冲突优先看 `chat.html` 与 `templates/layout/sidebar.html`；之后通常自动）。

<br/>

## 关于本仓库

本仓库是 [`zhayujie/CowAgent`](https://github.com/zhayujie/CowAgent) 的个人 fork，本 README 仅承载 fork 相对上游的改动说明。

> [!WARNING]
> ### ⚙️ 运行环境与上游不同：本 fork 使用项目内虚拟环境 `.venv`
>
> 上游把依赖装进系统 Python 的 user site 并常用 `--break-system-packages`；本 fork
> 改为**项目内隔离 venv**（`.venv/`，由 `uv venv --python 3.12` 创建），服务由
> systemd `cowagent.service` 指向 `.venv/bin/python` 启动。
>
> - 装包：`uv pip install --python .venv/bin/python <pkg>`（venv 无 `pip` 模块，**不要**用系统 `pip3`）
> - 测试：`.venv/bin/python -m pytest tests/ -q`
> - `cow` CLI：`.venv/bin/cow`（非 `~/.local/bin/cow`）
> - **不要卸载** `~/.local` 下的系统包来“清理环境”——曾因误删 `httpx` 导致飞书通道全部无法启动
>
> 面向 AI 助手的详细约定见 [`AGENTS.md`](./AGENTS.md)。

完整的产品介绍、安装指南、模型 / 通道 / 技能 / 记忆 / 知识库 / 多智能体 / 架构 / 更新日志等内容，请参阅上游 README：

- 英文：<https://github.com/zhayujie/CowAgent/blob/master/README.md>
- 简体中文：<https://github.com/zhayujie/CowAgent/blob/master/docs/zh/README.md>
- 繁體中文：<https://github.com/zhayujie/CowAgent/blob/master/docs/zh/README-Hant.md>
- 日本語：<https://github.com/zhayujie/CowAgent/blob/master/docs/ja/README.md>