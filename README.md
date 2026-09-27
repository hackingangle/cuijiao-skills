# 萃角儿 Skills

这是 `hackingangle/cuijiao-skills` 的独立技能仓。它提供 `cuijiao-sync`、`cuijiao-platform` 两个管道技能，并把平台智能体投影到 Cursor、Claude Code、Codex、OpenClaw、Hermes。本仓不保存 Token 或智能体私有人设。

## 当前接入状态

安装器要求 `https://<服务主机>/api`（本地开发可用 `http://127.0.0.1:<端口>/api`）提供：

1. `GET /api/projects`，Bearer Token 鉴权，返回项目数组。
2. `GET /api/agents`，同一 Token 鉴权，返回智能体数组。每项至少有正整数 `id`、字符串 `name`、字符串 `system_prompt`；`description` 可选。空账号还需支持 `POST /api/agents/ensure-defaults`，安装器会自动补种默认智能体。
3. 用户可签发、撤销的独立 API Token，能读取项目和智能体，能访问需要的素材接口。

`cc-b` 整合分支已实现前三项 API；尚未部署到生产。若目标服务缺 `GET /api/agents`，安装器会在任何写入前停止，明确提示服务端功能未就绪。文件/PDF/ASR 能力仍在迁移中。

## 本地验证与安装

在本目录运行：

```bash
python3 -m unittest discover -s tests -v
python3 setup-cuijiao.py "https://<服务主机>/api"
python3 check-skills.py
```

服务端完成上述依赖后，安装器交互式读取 API Token，保存到权限为 `0600` 的 `~/.cuijiao/env`。更新时沿用该文件中的地址与 Token；可再次传入地址覆盖地址。不要把 Token 写进命令行、仓库文件或网页截图。`~/.heimdall` 及旧 `heimdall-*` 技能不会被改动。未检测到客户端时可用 `CUIJIAO_SKILLS_DIRS` 指定技能目录（shell 风格引用，多个目录以空格分隔）。

## 公开分发入口

公开仓库 `main` 的安装与检查入口为：

```bash
curl -fsSL https://raw.githubusercontent.com/hackingangle/cuijiao-skills/main/setup-cuijiao.py | python3 - "https://<服务主机>/api"
curl -fsSL https://raw.githubusercontent.com/hackingangle/cuijiao-skills/main/check-skills.py | python3
```

使用前须确保服务端部署了项目、Agent 和 API Token 接口。开发验证使用真实 API Token 覆盖安装、智能体更新和撤销；这不代表生产服务已上线。
