#!/usr/bin/env python3
"""Validate local skills and marketplace registrations."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
MARKETPLACE_PATH = ROOT / ".claude-plugin" / "marketplace.json"
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


def discover_skill_dirs() -> list[Path]:
    skill_files = sorted(SKILLS_ROOT.glob("**/SKILL.md"))
    return [path.parent for path in skill_files]


def extract_name_from_frontmatter(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError("missing or malformed YAML frontmatter")

    frontmatter = match.group(1).splitlines()
    for line in frontmatter:
        key, sep, value = line.partition(":")
        if sep and key.strip() == "name":
            name = value.strip().strip("'\"")
            if not name:
                raise ValueError("frontmatter 'name' is empty")
            if not NAME_PATTERN.match(name):
                raise ValueError(
                    "frontmatter 'name' must be kebab-case (lowercase letters, numbers, hyphens)"
                )
            return name

    raise ValueError("frontmatter missing required 'name'")


def run_command(args: Iterable[str]) -> tuple[int, str]:
    result = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
    return result.returncode, output


def validate_with_skills_ref(skill_dir: Path) -> tuple[bool, str]:
    for command in ("agentskills", "skills-ref"):
        try:
            code, output = run_command([command, "validate", str(skill_dir)])
        except FileNotFoundError:
            continue

        if code == 0:
            return True, f"{command} validate passed"
        return False, f"{command} validate failed for {skill_dir}:\n{output}"

    return False, "Could not find 'agentskills' or 'skills-ref' CLI. Install skills-ref."


def load_marketplace_skill_names() -> set[str]:
    try:
        data = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"marketplace file not found: {MARKETPLACE_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {MARKETPLACE_PATH}: {exc}") from exc

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError("'plugins' must be a list in marketplace.json")

    names: set[str] = set()
    for plugin in plugins:
        if not isinstance(plugin, dict):
            raise ValueError("each entry in 'plugins' must be an object")
        skills = plugin.get("skills", [])
        if not isinstance(skills, list):
            raise ValueError("each plugin 'skills' value must be a list")
        for skill in skills:
            if isinstance(skill, str):
                name = skill
            elif isinstance(skill, dict) and isinstance(skill.get("name"), str):
                name = skill["name"]
            else:
                raise ValueError(
                    "each skill entry must be a string or an object containing string key 'name'"
                )
            names.add(name)

    return names


def main() -> int:
    errors: list[str] = []

    skill_dirs = discover_skill_dirs()
    if not skill_dirs:
        errors.append(f"No SKILL.md files found under {SKILLS_ROOT}")

    local_skill_names: set[str] = set()
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        try:
            skill_name = extract_name_from_frontmatter(skill_md)
        except ValueError as exc:
            errors.append(f"{skill_md}: {exc}")
            continue

        if skill_name in local_skill_names:
            errors.append(f"Duplicate skill name found in frontmatter: {skill_name}")
        local_skill_names.add(skill_name)

        ok, message = validate_with_skills_ref(skill_dir)
        if not ok:
            errors.append(message)

    try:
        marketplace_skill_names = load_marketplace_skill_names()
    except ValueError as exc:
        errors.append(str(exc))
        marketplace_skill_names = set()

    missing_in_marketplace = sorted(local_skill_names - marketplace_skill_names)
    unknown_in_marketplace = sorted(marketplace_skill_names - local_skill_names)

    if missing_in_marketplace:
        errors.append(
            "Skills missing from .claude-plugin/marketplace.json: "
            + ", ".join(missing_in_marketplace)
        )

    if unknown_in_marketplace:
        errors.append(
            "Skills listed in .claude-plugin/marketplace.json but not found locally: "
            + ", ".join(unknown_in_marketplace)
        )

    if errors:
        print("Validation failed:\n")
        for item in errors:
            print(f"- {item}")
        return 1

    print(
        "Validation passed: "
        f"{len(local_skill_names)} local skill(s) validated and marketplace registrations match."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
