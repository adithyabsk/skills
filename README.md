# adithyabsk-agent-skills

Personal Agent Skills marketplace and skill library.

This repository contains:
- custom skills under `skills/`
- marketplace metadata in `.claude-plugin/marketplace.json`
- CI + local validation tooling to ensure skills are valid and registered

## Install this marketplace in Claude Code

Add this repository as a plugin marketplace:

```bash
/plugin marketplace add adithyabsk/skills
/plugin install all-skills@adithyabsk-agent-skills
```

## Install upstream skill-creator

To work on skills in this repo with automated authoring/evaluation help, install the upstream document skills plugin and use `skill-creator`:

```bash
/plugin marketplace add anthropics/skills
/plugin install example-skills@anthropic-agent-skills
```

Then invoke it in your agent session when editing skills:
- `Use /example-skills:skill-creator ...`

## Repository structure

- `skills/` — local skills (each skill has a `SKILL.md`)
- `.claude-plugin/marketplace.json` — plugin/marketplace definition
- `.github/scripts/validate_skills.py` — validation script
- `.github/workflows/validate-skills.yml` — CI workflow for validation

## Local development

This repo uses [`uv`](https://docs.astral.sh/uv/) for Python tooling and dev dependencies.

### 1) Create local virtual environment and install dev dependencies

```bash
uv sync
```

### 2) Run validation locally

```bash
uv run python .github/scripts/validate_skills.py
```

The validator checks:
- every local `skills/**/SKILL.md` validates with `skills-ref`
- every local skill is registered in `.claude-plugin/marketplace.json`
- no stale marketplace entries exist for missing local skills

## CI validation

GitHub Actions runs `.github/workflows/validate-skills.yml` on pull requests and pushes to `main`.

It performs:
1. `uv sync --locked`
2. `uv run python .github/scripts/validate_skills.py`

## Adding a new skill

1. Create a folder `skills/<skill-name>/`.
2. Add `skills/<skill-name>/SKILL.md` with valid frontmatter:

```yaml
---
name: your-skill-name
description: What this skill does and when to use it.
---
```

3. Register the skill in `.claude-plugin/marketplace.json` under `plugins[].skills`.
4. (Recommended) Use upstream `skill-creator` to refine/evaluate prompts and instructions.
5. Run local validation:

```bash
uv run python .github/scripts/validate_skills.py
```

## Upstream references

This project follows the open Agent Skills format. For canonical docs and examples:
- Agent Skills spec: https://agentskills.io/specification
- skills-ref package: https://pypi.org/project/skills-ref/
- Agent Skills repo (spec + reference SDK): https://github.com/agentskills/agentskills
- Anthropic skills examples (includes document skills): https://github.com/anthropics/skills
