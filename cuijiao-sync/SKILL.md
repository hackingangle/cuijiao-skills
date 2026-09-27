---
name: cuijiao-sync
description: >
  安装或更新萃角儿的管道技能与平台智能体本机投影。
  当用户要求同步智能体、安装到 Cursor、Claude Code、Codex、OpenClaw、Hermes，或检查本机技能版本时使用。
---

# 萃角儿智能体同步

平台智能体是人设真源。本机 `cuijiao-agent-{id}` 文件只是投影；要修改人设，请在平台修改后重新运行安装器。

cc-b 整合代码已提供独立 API Token 和 `GET /api/agents`，目标服务仍需部署对应版本。先通过登录会话调用 `POST /api/tokens` 签发 `hd_` API Token；Token 管理接口不接受 API Token。安装器会用该 Token 预检 `GET /api/projects` 和 `GET /api/agents`；若接口缺失或鉴权失败，它会报错并停止，不写入 `~/.cuijiao/env`，也不安装技能。

## 安装与更新

从公开仓库 `main` 安装或更新：

```bash
curl -fsSL https://raw.githubusercontent.com/hackingangle/cuijiao-skills/main/setup-cuijiao.py | python3 - "https://<服务主机>/api"
```

也可在本地源码目录执行 `python3 setup-cuijiao.py "https://<服务主机>/api"`。已有 `~/.cuijiao/env` 时可省略地址。安装器交互式读取 API Token，保存在权限为 `0600` 的 `~/.cuijiao/env`。它只写 `cuijiao-*` 文件，不读取或更改 `~/.heimdall`。

| 客户端 | 管道技能 | 智能体投影 |
|---|---|---|
| Cursor | `~/.cursor/skills/cuijiao-{sync,platform}` | `~/.cursor/skills/cuijiao-agent-{id}` |
| Claude Code | `~/.claude/skills/cuijiao-{sync,platform}` | `~/.claude/agents/cuijiao-agent-{id}.md` |
| Codex | `~/.agents/skills/cuijiao-{sync,platform}` | `~/.agents/skills/cuijiao-agent-{id}` |
| OpenClaw | `~/.openclaw/skills/cuijiao-{sync,platform}` | `~/.openclaw/skills/cuijiao-agent-{id}` |
| Hermes | `~/.hermes/skills/cuijiao/cuijiao-{sync,platform}` | `~/.hermes/skills/cuijiao/cuijiao-agent-{id}` |

平台删掉的托管智能体投影会在下次同步时删除；安装器不会删其他文件。手改投影会在下次同步时被覆盖。

## 检查版本

本地源码目录运行 `python3 check-skills.py`。通过公开仓库检查：

```bash
curl -fsSL https://raw.githubusercontent.com/hackingangle/cuijiao-skills/main/check-skills.py | python3
```

退出码：`0` 与记录的安装源一致，`1` 缺少或过期，`2` 无安装记录或无法比对。此检查只比对管道技能；智能体人设变化需重跑安装器。
