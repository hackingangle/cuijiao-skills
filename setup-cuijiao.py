#!/usr/bin/env python3
"""Install Cuijiao pipeline skills and project user-owned agents to local harnesses."""

from __future__ import annotations

import getpass
import json
import os
import shlex
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


RAW = "https://raw.githubusercontent.com/hackingangle/cuijiao-skills/main"
HOME = Path.home()
CONFIG = HOME / ".cuijiao"
ENV = CONFIG / "env"
PIPE_SKILLS = ("cuijiao-sync", "cuijiao-platform")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fail(message: str) -> None:
    raise SystemExit(message)


def validate_base(value: str) -> str:
    base = value.rstrip("/")
    url = urlsplit(base)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.path != "/api"
        or (url.scheme == "http" and url.hostname not in {"localhost", "127.0.0.1", "::1"})
    ):
        fail("API 地址须为 https://<主机>/api；本机开发可用 http://127.0.0.1:<端口>/api")
    return base


def saved_env() -> dict[str, str]:
    if not ENV.is_file():
        return {}
    values: dict[str, str] = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("export "):
            parts = shlex.split(line)
            if len(parts) == 2 and "=" in parts[1]:
                key, value = parts[1].split("=", 1)
                values[key] = value
    return values


def request(url: str, token: str | None = None) -> tuple[int, bytes]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        opener = urllib.request.build_opener(NoRedirect)
        with opener.open(urllib.request.Request(url, headers=headers), timeout=15) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except urllib.error.URLError as error:
        fail(f"无法连接 {url}：{error.reason}")


def api_list(base: str, path: str, token: str) -> list[dict[str, object]]:
    status, body = request(f"{base}/{path}", token)
    if status == 404:
        fail("Agent 接口尚未就绪（GET /api/agents 返回 404）；没有安装任何技能。" if path == "agents"
             else "项目接口尚未就绪（GET /api/projects 返回 404）；没有安装任何技能。")
    if status != 200:
        fail(f"GET /api/{path} 返回 HTTP {status}；没有安装任何技能。")
    try:
        items = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        fail(f"GET /api/{path} 返回无效 JSON；没有安装任何技能。")
    if not isinstance(items, list):
        fail(f"GET /api/{path} 应返回数组；没有安装任何技能。")
    return items


def harnesses() -> tuple[list[Path], Path | None]:
    manual = os.environ.get("CUIJIAO_SKILLS_DIRS")
    if manual:
        roots = [Path(path).expanduser() for path in shlex.split(manual)]
        claude = HOME / ".claude/agents" if HOME / ".claude/skills" in roots else None
        return roots, claude

    roots: list[Path] = []
    claude: Path | None = None
    if shutil.which("claude") or (HOME / ".claude").exists():
        roots.append(HOME / ".claude/skills")
        claude = HOME / ".claude/agents"
    if (HOME / ".cursor").exists():
        roots.append(HOME / ".cursor/skills")
    if shutil.which("codex") or (HOME / ".codex").exists():
        roots.append(HOME / ".agents/skills")
    if shutil.which("openclaw") or (HOME / ".openclaw").exists():
        roots.append(HOME / ".openclaw/skills")
    if shutil.which("hermes") or (HOME / ".hermes").exists():
        roots.append(HOME / ".hermes/skills/cuijiao")
    return roots, claude


def source_skills() -> tuple[str, dict[str, bytes]]:
    local = Path(__file__).resolve().parent if not __file__.startswith("<") else None
    if local and all((local / name / "SKILL.md").is_file() for name in PIPE_SKILLS):
        return str(local), {name: (local / name / "SKILL.md").read_bytes() for name in PIPE_SKILLS}
    files: dict[str, bytes] = {}
    for name in PIPE_SKILLS:
        status, body = request(f"{RAW}/{name}/SKILL.md")
        if status != 200:
            fail(f"下载 {name} 失败（HTTP {status}）；没有安装任何技能。")
        files[name] = body
    return RAW, files


def validate_agents(items: list[dict[str, object]]) -> list[dict[str, object]]:
    agents: list[dict[str, object]] = []
    for item in items:
        if (
            not isinstance(item, dict)
            or type(item.get("id")) is not int
            or item["id"] <= 0
            or not isinstance(item.get("name"), str)
            or not isinstance(item.get("system_prompt"), str)
        ):
            fail("GET /api/agents 缺少 id、name 或 system_prompt；没有安装任何技能。")
        agents.append(item)
    if not agents:
        fail("平台尚无智能体；请先在应用中创建，再运行安装命令。没有安装任何技能。")
    return agents


def write_env(base: str, token: str) -> None:
    CONFIG.mkdir(mode=0o700, exist_ok=True)
    CONFIG.chmod(0o700)
    fd, temporary = tempfile.mkstemp(dir=CONFIG, prefix=".env-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(f"export CUIJIAO_API_BASE={shlex.quote(base)}\n")
            file.write(f"export CUIJIAO_API_TOKEN={shlex.quote(token)}\n")
        os.replace(temporary, ENV)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def agent_content(item: dict[str, object]) -> str:
    agent_id = item["id"]
    name = item["name"]
    description = item.get("description") or f"萃角儿智能体「{name}」"
    prompt = str(item["system_prompt"]).rstrip()
    return (
        "---\n"
        f"name: cuijiao-agent-{agent_id}\n"
        f"description: {json.dumps(str(description), ensure_ascii=False)}\n"
        "---\n\n"
        f"<!-- cuijiao-managed:{agent_id} -->\n\n"
        f"# {name}\n\n"
        "访问萃角儿项目和素材时遵守 cuijiao-platform。\n\n"
        f"{prompt}\n"
    )


def check_agent_targets(agents: list[dict[str, object]], roots: list[Path], claude: Path | None) -> None:
    for item in agents:
        agent_id = item["id"]
        slug = f"cuijiao-agent-{agent_id}"
        targets = [root / slug / "SKILL.md" for root in roots if root != HOME / ".claude/skills"]
        if claude:
            targets.append(claude / f"{slug}.md")
        for path in targets:
            if path.is_symlink() or (path.exists() and (
                not path.is_file() or f"<!-- cuijiao-managed:{agent_id} -->" not in path.read_text(encoding="utf-8")
            )):
                fail(f"已有非托管智能体文件：{path}；没有安装任何技能。")


def sync_agents(agents: list[dict[str, object]], roots: list[Path], claude: Path | None) -> None:
    ids = {str(item["id"]) for item in agents}
    for item in agents:
        slug = f"cuijiao-agent-{item['id']}"
        body = agent_content(item)
        for root in roots:
            if root == HOME / ".claude/skills":
                continue
            dest = root / slug / "SKILL.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
        if claude:
            dest = claude / f"{slug}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")

    for root in roots:
        if root == HOME / ".claude/skills":
            continue
        for path in root.glob("cuijiao-agent-*/SKILL.md"):
            if "<!-- cuijiao-managed:" not in path.read_text(encoding="utf-8"):
                continue
            if path.parent.name.removeprefix("cuijiao-agent-") not in ids:
                path.unlink()
                try:
                    path.parent.rmdir()
                except OSError:
                    pass
    if claude:
        for path in claude.glob("cuijiao-agent-*.md"):
            if "<!-- cuijiao-managed:" in path.read_text(encoding="utf-8") and path.stem.removeprefix("cuijiao-agent-") not in ids:
                path.unlink()


def main() -> None:
    saved = saved_env()
    base = validate_base(sys.argv[1] if len(sys.argv) > 1 else saved.get("CUIJIAO_API_BASE", ""))
    token = saved.get("CUIJIAO_API_TOKEN") or getpass.getpass("请输入萃角儿 API Token：").strip()
    if not token:
        fail("缺少 API Token；请在应用中签发后重试。")

    api_list(base, "projects", token)
    agents = validate_agents(api_list(base, "agents", token))
    roots, claude = harnesses()
    if not roots:
        fail("未检测到 Cursor、Claude Code、Codex、OpenClaw 或 Hermes；可设置 CUIJIAO_SKILLS_DIRS。")
    source, skills = source_skills()
    check_agent_targets(agents, roots, claude)

    write_env(base, token)
    for root in roots:
        for name, body in skills.items():
            dest = root / name / "SKILL.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
    sync_agents(agents, roots, claude)
    (CONFIG / "skills.lock").write_text(
        f"source={source}\ntargets={json.dumps([str(root) for root in roots])}\n",
        encoding="utf-8",
    )
    (CONFIG / "agents.lock").write_text(
        f"count={len(agents)}\nids={','.join(str(item['id']) for item in agents)}\n",
        encoding="utf-8",
    )
    print(f"已安装到 {len(roots)} 个 Harness，并同步 {len(agents)} 个智能体。")
    print("在 Harness 终端执行：source ~/.cuijiao/env")


if __name__ == "__main__":
    main()
