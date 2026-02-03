# Odometer Labs

## Carputer GPS Tracking System

### Getting Started

Clone the repository using SSH (recommended):
```bash
git clone git@github.com:odometer-labs/carputer.git
```

Or via HTTPS:
```bash
git clone https://github.com/odometer-labs/carputer.git
```

## Branch Naming Convention

Use the following format for all branches:

```
[type]/[subteam]/story_name
```

### Types

**dev/** - New features and functionality (e.g., `dev/fe/user-authentication`, `dev/be/gps-parser`)

**bugfix/** - Routine bug fixes (e.g., `bugfix/emb/aprs-timeout`, `bugfix/fe/map-rendering`)

**refactor/** - Code improvements without changing functionality (e.g., `refactor/be/database-queries`, `refactor/infra/ci-pipeline`)

### Subteams

- **fe** - Frontend
- **be** - Backend
- **infra** - Infrastructure
- **emb** - Embedded systems

## Git Workflow

### Starting Work

Update your local main branch:
```bash
git checkout main
git pull
```

Create a new branch following the naming convention:
```bash
git checkout -b dev/fe/offline-map-cache
```

### Committing Changes

Commit regularly and push at the end of your session:
```bash
git push origin dev/fe/offline-map-cache
```

Once your feature is complete and tested, open a pull request on GitHub targeting the `main` branch.

### Syncing with Main

To incorporate recent changes from main into your feature branch:

```bash
git checkout your-feature-branch
git merge origin/main
```

Resolve any conflicts as needed.

**Alternative: Rebase for cleaner history**

If you're working independently or want a linear history:
```bash
git rebase origin/main
```

Rebasing rewrites your branch's commit history on top of main, avoiding merge commits.
