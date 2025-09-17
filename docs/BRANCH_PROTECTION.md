# Branch Protection Playbook

Configure branch protection in the GitHub UI for `main` (and future `release/*` branches) to enforce guardrails.

## Required Settings
1. Protect branches: specify `main` (and add `release/*` when applicable).
2. Require pull request before merging.
   - Require approvals: minimum 1.
   - Require review from Code Owners.
   - Dismiss stale approvals.
   - Disallow any bypass permissions.
3. Require status checks before merging.
   - Require branches to be up to date before merging.
   - Mark these checks as required: `CI`, `Route Compliance`, `Smoke`.
4. Require conversation resolution before merging (recommended).
5. Require signed commits (optional but encouraged).
6. Disallow force pushes and deletions on protected branches.

## Configuration Steps
1. Open GitHub → **Settings › Branches › Branch protection rules**.
2. Add or edit the rule for `main`.
3. Apply the settings above and save.
4. Repeat for `release/*` rules when release branches are introduced.
5. Verify by attempting merges without approvals/checks to ensure protection holds.

Document updates in release checklists to prevent drift.
