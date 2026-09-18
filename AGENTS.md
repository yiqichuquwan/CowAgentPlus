# AGENTS.md — CowAgentPlus fork

本文件面向在此仓库工作的 AI 编码助手。**先读这里，再动手。**

## 这是 fork，不是上游

- 上游：`zhayujie/CowAgent`（远端名 `upstream`）
- 本仓库：`yiqichuquwan/CowAgentPlus`（远端名 `origin`，开发分支 `dev`）
- 同步上游：`git fetch upstream && git merge upstream/master`（在 `dev` 上）
- fork 相对上游的私有改动清单见 `README.md` 顶部表格。

## 关键差异：本 fork 用项目内虚拟环境（.venv），上游不用

**这是本 fork 与上游最重要的运行环境差异，改动依赖/运行脚本时必须遵守。**

上游 `run.sh` 默认把依赖装进系统 Python（`/usr/bin/python3`）的 user site
（`~/.local/lib/python3.12/site-packages`），并常用 `--break-system-packages`。
本 fork 改为**项目内隔离 venv**：

| 项目 | 本 fork | 上游 |
| --- | --- | --- |
| 解释器 | `/home/user/qiut/Code/CowAgent/.venv/bin/python` | `/usr/bin/python3` |
| 依赖位置 | `.venv/lib/python3.12/site-packages` | `~/.local/lib/python3.12/site-packages` |
| `cow` CLI | `.venv/bin/cow` | `~/.local/bin/cow` |
| venv 创建者 | `uv venv --python 3.12 .venv` | 无 venv |
| pip | venv **无** `pip` 模块，用 `uv pip --python .venv/bin/python` | `python3 -m pip` |
| 服务启动 | systemd `cowagent.service` → `.venv/bin/python app.py` | 系统 python |

### 因此，在本仓库中：

1. **装包一律用 `uv pip`，不要用系统 `pip3`，也不要 `--break-system-packages`：**
   ```bash
   uv pip install --python .venv/bin/python <pkg>
   ```
   可选依赖见 `requirements-optional.txt`（当前**未安装**；注意其中
   `websocket-client==1.2.0` 与 `requirements.txt` 的 `>=1.4.0` 冲突，需跳过该项）。

2. **运行测试 / 脚本用 `.venv/bin/python`：**
   ```bash
   .venv/bin/python -m pytest tests/ -q
   ```

3. **`run.sh` 已感知 venv**（`detect_python_command` 优先探测 `.venv/bin/python`，
   `pip_cmd()` 在无 pip 时回退到 `uv pip`）。改 `run.sh` 时不要退回裸
   `$PYTHON_CMD -m pip`，保持 `${PIP_CMD:-$PYTHON_CMD -m pip}` 形式。

4. **不要 `pip uninstall` 系统 `~/.local` 里的包**去“清理环境”——本 fork 运行
   在 venv 内，系统包与运行无关，误删会伤害其他工具（此仓库曾因误删 `httpx`
   导致飞书通道全挂）。

5. systemd 单元在仓库外：`~/.config/systemd/user/cowagent.service`，其中
   `ExecStart` 指向 `.venv/bin/python`，并设 `Environment=PATH=.../.venv/bin:...`
   以便 agent 的 bash 子进程也用 venv 解释器。

## 测试套件说明

- 全量：`.venv/bin/python -m pytest tests/ -q`
- 部分测试依赖宿主的 `config.json`（含 `cow_lang`、真实 workspace）与可选依赖；
  不要在测试里依赖宿主语言/路径，改用 fixture 保存恢复。
- 若新增测试桩替换 `sys.modules["requests"]` 等，务必在完成后还原，避免污染后续测试。

## 提交与同步约定

- 开发在 `dev` 分支；提交信息用中文，格式参考现有 `git log`。
- 未经用户明确要求，不要 `commit` / `push`。
