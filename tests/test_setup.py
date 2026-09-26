"""Exercise the local installer without touching the real home directory."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class API(BaseHTTPRequestHandler):
    agents: list[dict[str, object]] | None = None
    token = "test-token-without-prefix"

    def do_GET(self) -> None:
        if self.headers.get("Authorization") != f"Bearer {self.token}":
            self.respond(401, {"error": "unauthorized"})
        elif self.path == "/api/projects":
            self.respond(200, [])
        elif self.path == "/api/agents" and self.agents is not None:
            self.respond(200, self.agents)
        else:
            self.respond(404, {"error": "not_found"})

    def respond(self, status: int, body: object) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args: object) -> None:
        pass


class InstallerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        API.token = "test-token-without-prefix"
        for name in (".cursor", ".claude", ".codex", ".openclaw", ".hermes"):
            (self.home / name).mkdir()
        API.agents = [{"id": 7, "name": "写稿", "description": "写脚本", "system_prompt": "只用所选素材。"}]
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), API)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.api_base = f"http://127.0.0.1:{self.server.server_port}/api"
        config = self.home / ".cuijiao"
        config.mkdir(mode=0o700)
        self.env_file = config / "env"
        self.env_file.write_text(
            f"export CUIJIAO_API_BASE='{self.api_base}'\n"
            f"export CUIJIAO_API_TOKEN='{API.token}'\n"
        )
        self.env_file.chmod(0o600)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def run_script(self, name: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / name)],
            cwd=ROOT,
            env={**os.environ, "HOME": str(self.home)},
            text=True,
            capture_output=True,
            check=False,
        )

    def test_missing_agent_api_does_not_install_partial_skills(self) -> None:
        API.agents = None
        original_env = self.env_file.read_bytes()

        result = self.run_script("setup-cuijiao.py")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Agent 接口尚未就绪", result.stderr)
        self.assertEqual(self.env_file.read_bytes(), original_env)
        self.assertFalse((self.home / ".cursor/skills/cuijiao-sync/SKILL.md").exists())
        self.assertNotIn(API.token, result.stdout + result.stderr)

    def test_installs_five_harnesses_and_checks_local_skill_versions(self) -> None:
        old_skill = self.home / ".cursor/skills/heimdall-platform/SKILL.md"
        old_skill.parent.mkdir(parents=True)
        old_skill.write_text("old Heimdall skill")

        result = self.run_script("setup-cuijiao.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        roots = (
            self.home / ".cursor/skills",
            self.home / ".claude/skills",
            self.home / ".agents/skills",
            self.home / ".openclaw/skills",
            self.home / ".hermes/skills/cuijiao",
        )
        for root in roots:
            self.assertTrue((root / "cuijiao-sync/SKILL.md").is_file())
            self.assertTrue((root / "cuijiao-platform/SKILL.md").is_file())
        self.assertTrue((self.home / ".claude/agents/cuijiao-agent-7.md").is_file())
        self.assertEqual(old_skill.read_text(), "old Heimdall skill")
        self.assertNotIn(API.token, result.stdout + result.stderr)
        self.assertEqual(self.env_file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.run_script("check-skills.py").returncode, 0)

        (roots[0] / "cuijiao-sync/SKILL.md").write_text("stale")
        self.assertEqual(self.run_script("check-skills.py").returncode, 1)

    def test_token_file_quotes_shell_characters(self) -> None:
        marker = self.home / "unexpected-shell-command"
        API.token = f"quote'$(touch {marker})"
        self.env_file.write_text(
            f"export CUIJIAO_API_BASE={shlex.quote(self.api_base)}\n"
            f"export CUIJIAO_API_TOKEN={shlex.quote(API.token)}\n"
        )

        result = self.run_script("setup-cuijiao.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        check = subprocess.run(
            ["/bin/sh", "-c", '. "$1"; [ "$CUIJIAO_API_TOKEN" = "$2" ]', "sh", str(self.env_file), API.token],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertFalse(marker.exists())
        self.assertNotIn(API.token, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
