#!/usr/bin/env python3
"""Compare installed Cuijiao pipeline skills with their recorded source."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path


SKILLS = ("cuijiao-sync", "cuijiao-platform")
LOCK = Path.home() / ".cuijiao/skills.lock"


def source_bytes(source: str, skill: str) -> bytes:
    if source.startswith("https://"):
        with urllib.request.urlopen(f"{source}/{skill}/SKILL.md", timeout=15) as response:
            return response.read()
    return (Path(source) / skill / "SKILL.md").read_bytes()


def main() -> int:
    if not LOCK.is_file():
        print(f"缺少安装记录：{LOCK}。先运行 setup-cuijiao.py。")
        return 2
    try:
        values = dict(line.split("=", 1) for line in LOCK.read_text(encoding="utf-8").splitlines())
        source = values["source"]
        targets = json.loads(values["targets"])
        if not isinstance(targets, list) or not targets or not all(isinstance(t, str) for t in targets):
            raise ValueError("targets 格式错误")
        expected = {skill: source_bytes(source, skill) for skill in SKILLS}
    except (OSError, KeyError, ValueError, json.JSONDecodeError, urllib.error.URLError) as error:
        print(f"无法比对技能：{error}")
        return 2

    stale = False
    for directory in targets:
        for skill in SKILLS:
            path = Path(directory) / skill / "SKILL.md"
            if not path.is_file() or path.read_bytes() != expected[skill]:
                print(f"待更新：{path}")
                stale = True
    if stale:
        print("请重新运行 setup-cuijiao.py。")
        return 1
    print("萃角儿管道技能与安装源一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
