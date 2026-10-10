# Agent instructions

## GitHub Actions cost policy

- Read [docs/ACTIONS_COST_POLICY.md](docs/ACTIONS_COST_POLICY.md) before changing workflows or requesting cloud checks.
- Run routine lint, tests, builds, browser QA, dependency audits and synthetic checks locally or on the existing isolated LAN QA environment. Use test data and keep secrets local.
- Do not dispatch or rerun Actions, push empty/test-only commits, enable disabled workflows, add schedules, duplicate push/PR checks or expand hosted runner matrices for routine development. An intentional cloud run needs explicit user authorization; existing mandatory release gates remain mandatory.
- Do not raise billing budgets, enable paid services or change payment methods. Never claim that skipped cloud checks passed, and never bypass a required release/security gate.
- Operational jobs (publishing, authenticated production checks, parser writes, maintenance or notifications) require their existing authorization and secrets; a local QA command does not authorize production side effects.
