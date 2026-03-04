# LinkedIn Post — dev-starter-kit

---

**COPY BELOW THIS LINE**

---

Every new project starts the same way:

No CI. No linting. No test enforcement. No issue templates.

Three weeks in, you're debugging a production incident with no runbook, your AI coding assistant is generating code that doesn't follow your conventions, and half the team is committing directly to main.

I kept solving this problem from scratch across multiple projects — a multi-cluster AI evaluation platform on GCP, Python evaluation pipelines, production microservices. The same patterns kept working.

So I extracted all of it into one open-source starter repo. But I added something the original projects didn't have: instruction files for every major AI coding tool.

**What's in it:**

CI/CD Workflows (GitHub Actions)
→ Ruff auto-fix with commit-back
→ Test coverage enforcement that posts PR comments with exact test file names and method signatures
→ Merge readiness gates

Pre-commit Hooks
→ Lint, format, syntax check, private key detection, branch protection

Issue Templates
→ Bug reports, incident reports, infrastructure issues — all structured

Incident Runbook
→ Severity classification, triage checklists, diagnostic commands, post-incident review template

AI Coding Tool Instructions
→ AGENTS.md (Codex, Cursor, Claude Code, Windsurf)
→ CLAUDE.md (Claude Code sessions)
→ .cursor/rules/ (modular, glob-scoped Cursor rules)
→ .github/copilot-instructions.md (GitHub Copilot)

The AI instructions teach your tools to:
• Read files before editing
• Run lint after every change
• Run tests after every change
• Write tests for new code
• Use conventional commits
• Never commit secrets

The result: your AI coding tool follows the same development loop a senior engineer would. It doesn't just generate code — it generates code that passes your CI.

Clone it. Customize it. Ship.

🔗 https://github.com/humzakt/dev-starter-kit
📝 Full deep-dive: https://humzakt.github.io/blog/dev-starter-kit-ai-coding-tools.html

MIT Licensed.

#OpenSource #AITools #DevOps #CI #GitHubActions #DeveloperExperience #Python #CursorIDE #ClaudeCode #Copilot #SoftwareEngineering
