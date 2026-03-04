# Medium Post — dev-starter-kit

**Title:** I Built a Starter Repo That Turns AI Coding Tools Into Senior Engineers

**Subtitle:** An open-source template with CI/CD, test coverage enforcement, incident runbooks, and pre-configured instructions for Cursor, Claude Code, Codex, and Copilot

**Tags:** AI, Software Engineering, Developer Experience, GitHub Actions, Open Source

---

**COPY BELOW THIS LINE**

---

## The Problem Every Project Has

Every new project starts the same way: create a repo, write some code, realize you have no CI, no linting, no test enforcement, no issue templates. Three weeks in, you're debugging a production incident with no runbook, your AI coding assistant is generating code that doesn't follow your conventions, and half the team is committing directly to main.

I've set up development practices across multiple production projects — from a multi-cluster AI evaluation platform on GCP to Python evaluation pipelines. The same patterns kept working: Ruff for linting with auto-fix in CI, pre-commit hooks that catch problems before they reach the remote, test coverage enforcement that posts PR comments telling you exactly which test files to create, and incident runbooks that turn 2-hour debugging sessions into 15-minute triage flows.

So I extracted all of it into a single, clone-and-go starter repo. But I added something the original projects didn't have: **instruction files for every major AI coding tool** — Cursor, Claude Code, Codex, and GitHub Copilot — configured to follow the same practices the CI enforces.

**The repo:** [github.com/humzakt/dev-starter-kit](https://github.com/humzakt/dev-starter-kit)

---

## AI Tools Without Context Are Junior Developers

AI coding tools are powerful, but out of the box they don't know your project's conventions. They'll use single quotes when your linter expects double quotes. They'll skip tests. They'll commit to main. They'll generate 200-character lines when your config says 120. They'll catch generic exceptions when your style guide says to be specific.

The fix isn't to stop using AI tools — it's to give them the same onboarding document you'd give a new team member. That's what `AGENTS.md`, `CLAUDE.md`, and `.cursor/rules/` files are for. They turn your AI assistant from a context-free code generator into something that understands your project's architecture, follows your conventions, and runs the right commands after every change.

---

## What's in the Starter Kit

### CI/CD Workflows

Three GitHub Actions workflows that work together:

**PR Checks** is the main quality gate. It runs Ruff with `--fix`, commits any auto-fixes back to your branch, then verifies the code is clean. After linting passes, it runs pytest. The interesting part is the test coverage enforcement: it detects which Python source files you changed, checks whether you also added or updated the corresponding test files, and if you didn't, it posts a PR comment with the exact test file names, class names, and method signatures you need to write.

**Lint & Format** runs on both pushes and PRs, but only checks files that actually changed.

**Merge Readiness** is the final gate — strict lint, Python syntax compilation, YAML validation, and tests. All must pass before merging.

### Pre-commit Hooks

Catches problems before they reach CI:
- Ruff lint and format on every commit
- Python syntax verification, YAML/JSON/TOML validation
- Trailing whitespace, line endings, end-of-file fixers
- Private key detection, large file prevention
- Branch protection — blocks direct commits to main

### Issue Templates

Three structured templates: Bug Reports (with component classification and priority), Incident Reports (SEV-1 through SEV-4 with triage checklists), and Infrastructure Issues (CI/CD, dependency, environment problems).

### Incident Runbook

A structured playbook with severity classification, 3-phase triage checklists, component-specific diagnostics, common failure scenarios, and a post-incident review template.

---

## The AI Tool Configuration Layer

This is the part that makes the starter kit different. Every major AI coding tool reads a different file format for project instructions:

| File | Tool | Purpose |
|------|------|---------|
| `AGENTS.md` | Codex, Cursor, Claude Code, Windsurf | Universal agent instructions |
| `CLAUDE.md` | Claude Code | Session-persistent instructions |
| `.cursor/rules/*.mdc` | Cursor IDE | Modular, glob-scoped rules |
| `.claude/rules/*.md` | Claude Code | Scoped rules with patterns |
| `.github/copilot-instructions.md` | GitHub Copilot | Code generation guidelines |

### What the Instructions Teach

All instruction files converge on the same core behaviors:

1. **Read before editing** — understand the existing code and its tests
2. **Run lint after every edit** — `ruff check --fix . && ruff format .`
3. **Run tests after every edit** — `pytest tests/ -v`
4. **Fix failures before moving on** — don't leave broken tests or lint errors
5. **Write tests for new code** — the CI enforces this anyway
6. **Use conventional commits** — `feat:`, `fix:`, `chore:`, etc.
7. **Never commit secrets** — use environment variables

The result: your AI coding tool follows the same development loop a senior engineer would.

---

## How to Use It

```bash
git clone https://github.com/humzakt/dev-starter-kit.git my-project
cd my-project
rm -rf .git
git init && git checkout -b main

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

Customize by updating `pyproject.toml` (project name, lint rules), issue templates (component dropdowns), and AI tool files (architecture section, project-specific commands).

---

## Design Decisions

**Why multiple AI tool files?** AGENTS.md is the most broadly compatible, but each tool has unique capabilities. Cursor's `.mdc` files support glob-based scoping. Claude Code supports hierarchical overrides. By including all formats, the starter kit works regardless of which tool your team uses.

**Why structural test coverage instead of coverage percentage?** Coverage percentage creates perverse incentives. The structural check is simpler: if you changed source files, did you also change test files?

**Why auto-fix in CI?** The alternative is rejecting PRs for formatting issues, which wastes everyone's time. CI fixes formatting and commits it back.

**Why pre-commit AND CI?** Pre-commit catches issues locally. CI catches issues when pre-commit is bypassed. Belt and suspenders.

---

## Takeaways

After implementing these practices across multiple production projects:

- **Auto-fix eliminated 90% of "fix formatting" follow-up commits**
- **PR comment guidance is more effective than just a red X on a check**
- **Incident runbooks pay for themselves the first time someone uses the triage checklist**
- **AI tool instructions compound** — every session where the AI follows your conventions saves correction time

The repo is MIT licensed. Clone it, customize it, ship it.

[github.com/humzakt/dev-starter-kit](https://github.com/humzakt/dev-starter-kit)

---

*Humza Tareen builds production AI systems at scale. More articles at [humzakt.github.io](https://humzakt.github.io).*
