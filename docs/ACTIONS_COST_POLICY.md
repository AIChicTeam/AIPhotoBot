# Local-first checks and GitHub Actions costs

Policy prepared in response to the user's explicit request on 2026-10-10. These projects must not incur unattended runner use for routine development.

## GitHub Actions cost policy

- Read [docs/ACTIONS_COST_POLICY.md](docs/ACTIONS_COST_POLICY.md) before changing workflows or requesting cloud checks.
- Run routine lint, tests, builds, browser QA, dependency audits and synthetic checks locally or on the existing isolated LAN QA environment. Use test data and keep secrets local.
- Do not dispatch or rerun Actions, push empty/test-only commits, enable disabled workflows, add schedules, duplicate push/PR checks or expand hosted runner matrices for routine development. An intentional cloud run needs explicit user authorization; existing mandatory release gates remain mandatory.
- Do not raise billing budgets, enable paid services or change payment methods. Never claim that skipped cloud checks passed, and never bypass a required release/security gate.
- Operational jobs (publishing, authenticated production checks, parser writes, maintenance or notifications) require their existing authorization and secrets; a local QA command does not authorize production side effects.

## Current cloud behavior

All editable workflow files on the default branch are manual-only. Locally reproducible CI workflows are additionally disabled in repository settings to prevent automatic runs from stale feature branches. To use one deliberately, obtain explicit authorization, enable it, dispatch the intended revision once, then disable it again. Do not rerun unchanged failures in a loop.

GitHub-generated Pages deployment workflows and Dependabot services were not disabled by this change. Pages publishing is a separate delivery mechanism; it is not a replacement for local QA. Existing production and security/release approval rules remain in force.

No editable GitHub Actions workflow was present during this audit.

## Local verification

Use the project's existing test/build scripts and documented QA environment. Inspect package scripts, pyproject/requirements or the Makefile and run the checks relevant to the changed files locally. Do not invent a passing result when a dependency or environment is unavailable.

Record the tested commit, commands and results. Local checks do not create a GitHub status check; a release rule requiring cloud evidence must be satisfied explicitly before publication. No production secrets, customer data or environment files may be uploaded to Actions or copied to LAN QA.

## Defaults for future changes

No new schedule, workflow_run fan-out, push/PR duplicate, hosted Windows matrix, paid runner or automated artifact upload without explicit owner authorization. Keep diagnostic artifact retention bounded for any approved cloud run. Cancellation and concurrency do not make a run free. Standard public-repository runners can be free, but avoid unnecessary execution there too. Keep security updates and deployment approval checks; reduce their execution frequency rather than falsely reporting success.
