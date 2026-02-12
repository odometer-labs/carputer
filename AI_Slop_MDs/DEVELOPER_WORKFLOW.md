# Carputer Developer Workflow Guide

This document outlines the standard development workflow for the Carputer GPS Tracking System. All team members should follow these practices to ensure consistent, high-quality contributions.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Git Workflow & Jira Integration](#git-workflow--jira-integration)
4. [Dependency Management with uv](#dependency-management-with-uv)
5. [Docker Development](#docker-development)
6. [API Development & OpenAPI](#api-development--openapi)
7. [Testing Requirements](#testing-requirements)
8. [Code Review & Merging](#code-review--merging)

---

## Getting Started

### 1. Clone the Repository

```bash
# SSH (recommended)
git clone git@github.com:odometer-labs/carputer.git

# HTTPS
git clone https://github.com/odometer-labs/carputer.git

cd carputer
```

### 2. Verify Prerequisites

Ensure you have the following installed:

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Git | 2.40+ | Version control |
| uv | 0.1+ | Python dependency management |
| Node.js | 20 LTS | Frontend development |

---

## Development Environment

### Starting the Docker Development Stack

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Start specific services only
docker compose up -d postgres redis api
```

### Service Endpoints (Local Development)

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Frontend | http://localhost:5173 | Svelte dev server |
| PostgreSQL | localhost:5432 | Database (PostGIS enabled) |
| Redis | localhost:6379 | Cache/message broker |

### Stopping the Environment

```bash
# Stop all services (preserves data)
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

---

## Git Workflow & Jira Integration

### Branch Naming Convention

All branches must follow this format and include the Jira ticket ID:

```
[type]/[subteam]/[JIRA-ID]-story-name
```

**Examples:**
- `dev/be/CARP-123-gps-parser`
- `bugfix/fe/CARP-456-map-rendering-fix`
- `refactor/infra/CARP-789-ci-optimization`

### Types

| Type | Use Case |
|------|----------|
| `dev/` | New features and functionality |
| `bugfix/` | Bug fixes |
| `refactor/` | Code improvements (no behavior change) |
| `hotfix/` | Urgent production fixes |

### Subteams

| Subteam | Domain |
|---------|--------|
| `fe` | Frontend (Svelte/TypeScript) |
| `be` | Backend (FastAPI/Go) |
| `infra` | Infrastructure/DevOps |
| `emb` | Embedded systems (Rust/C) |

### Daily Workflow

#### 1. Start Your Day

```bash
# Update local main
git checkout main
git pull origin main

# Find your Jira ticket and note the ID (e.g., CARP-123)
```

#### 2. Create a Feature Branch

```bash
# Create branch with Jira ID
git checkout -b dev/be/CARP-123-implement-smart-beaconing
```

#### 3. Work on Your Feature

Make commits with meaningful messages that reference the Jira ticket:

```bash
# Commit format: [JIRA-ID] Brief description
git add .
git commit -m "[CARP-123] Add smart beaconing algorithm"
git commit -m "[CARP-123] Add unit tests for beacon interval calculation"
```

#### 4. Push Regularly

Push at least once per work session:

```bash
git push origin dev/be/CARP-123-implement-smart-beaconing
```

#### 5. Keep Your Branch Updated

Sync with main at least daily to avoid large merge conflicts:

```bash
# Option A: Merge (preserves history)
git fetch origin
git merge origin/main

# Option B: Rebase (cleaner history, use for small branches)
git fetch origin
git rebase origin/main
```

### Jira Workflow Integration

| Jira Status | Git Action |
|-------------|------------|
| **To Do** | No branch created yet |
| **In Progress** | Branch created, active development |
| **In Review** | Pull request opened |
| **Done** | PR merged to main |

**Tip:** Use Jira's GitHub integration to automatically link commits and PRs to tickets.

---

## Dependency Management with uv

We use [uv](https://github.com/astral-sh/uv) for Python dependency management. It's faster than pip and provides deterministic builds.

### Initial Setup

```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Working with Dependencies

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install project dependencies from pyproject.toml
uv pip install -e ".[dev]"

# Or install from requirements.txt
uv pip install -r requirements.txt
```

### Adding New Dependencies

```bash
# Add a production dependency
uv pip install fastapi

# Add a development dependency
uv pip install pytest --dev

# After adding, update requirements files
uv pip compile pyproject.toml -o requirements.txt
uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
```

### Lock File Workflow

```bash
# Generate lock file for reproducible builds
uv pip compile pyproject.toml -o requirements.lock

# Install from lock file (CI/production)
uv pip sync requirements.lock
```

**Important:** Always commit updated `requirements.txt` and `requirements.lock` files with your PR.

---

## Docker Development

### Building Images

```bash
# Build all services
docker compose build

# Build specific service
docker compose build api

# Build without cache (after dependency changes)
docker compose build --no-cache api
```

### Running Commands in Containers

```bash
# Run a one-off command
docker compose exec api python manage.py migrate

# Open a shell in the API container
docker compose exec api /bin/bash

# Run tests in container
docker compose exec api pytest
```

### Database Operations

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U carputer -d carputer

# Run migrations
docker compose exec api alembic upgrade head

# Create a new migration
docker compose exec api alembic revision --autogenerate -m "Add new_road table"
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps api

# Last 100 lines
docker compose logs --tail=100 api
```

### Troubleshooting

```bash
# Check container status
docker compose ps

# Restart a specific service
docker compose restart api

# Rebuild and restart
docker compose up -d --build api

# Full reset (nuclear option)
docker compose down -v && docker compose up -d --build
```

---

## API Development & OpenAPI

We use FastAPI with automatic OpenAPI (Swagger) documentation generation.

### OpenAPI Specification Structure

All API endpoints should follow this structure:

```
/api/v1/
├── /tracks
│   ├── GET    /              - List all tracks
│   ├── POST   /              - Create new track
│   ├── GET    /{track_id}    - Get track by ID
│   ├── PUT    /{track_id}    - Update track
│   ├── DELETE /{track_id}    - Delete track
│   └── GET    /{track_id}/points - Get track points
│
├── /positions
│   ├── GET    /current       - Get current GPS position
│   ├── POST   /              - Record new position
│   └── WS     /stream        - WebSocket for real-time positions
│
├── /roads
│   ├── GET    /              - List discovered roads
│   ├── GET    /new           - List newly discovered roads
│   └── GET    /{road_id}     - Get road details
│
└── /aprs
    ├── GET    /stations      - List nearby APRS stations
    └── GET    /history       - Get APRS packet history
```

### Writing API Endpoints

Follow these conventions for all FastAPI endpoints:

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/v1/tracks", tags=["Tracks"])

class TrackCreate(BaseModel):
    """Schema for creating a new track."""
    name: str = Field(..., min_length=1, max_length=100, example="Morning Commute")
    description: str | None = Field(None, max_length=500)

class TrackResponse(BaseModel):
    """Schema for track response."""
    id: int
    name: str
    description: str | None
    created_at: datetime
    distance_meters: float
    
    class Config:
        from_attributes = True

@router.post(
    "/",
    response_model=TrackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new track",
    description="Creates a new GPS track with the given name and optional description.",
    responses={
        201: {"description": "Track created successfully"},
        422: {"description": "Validation error"},
    }
)
async def create_track(track: TrackCreate) -> TrackResponse:
    """
    Create a new GPS track.
    
    - **name**: Display name for the track (required)
    - **description**: Optional description of the track
    """
    # Implementation here
    pass
```

### API Documentation Requirements

Every endpoint must include:

1. **Pydantic models** for request/response schemas
2. **Field descriptions** with examples
3. **HTTP status codes** documented in responses
4. **Docstrings** for the Swagger UI description
5. **Tags** for grouping related endpoints

### Accessing API Documentation

| URL | Format |
|-----|--------|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc (readable) |
| http://localhost:8000/openapi.json | Raw OpenAPI JSON spec |

### Exporting OpenAPI Spec

```bash
# Export for external tools or API clients
curl http://localhost:8000/openapi.json > openapi.json

# Generate TypeScript types from spec (for frontend)
npx openapi-typescript openapi.json -o frontend/src/api/types.ts
```

---

## Testing Requirements

### Test Categories

| Type | Location | Runs When |
|------|----------|-----------|
| Unit Tests | `tests/unit/` | Every commit, PR |
| Integration Tests | `tests/integration/` | PR, merge to main |
| E2E Tests | `tests/e2e/` | Nightly, release |

### Unit Testing Standards

**Before opening a PR, developers must:**

1. Write unit tests for all new functions/methods
2. Achieve minimum **80% code coverage** on new code
3. Ensure all existing tests pass

### Running Tests Locally

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_smart_beaconing.py

# Run tests matching a pattern
pytest -k "test_beacon"

# Run tests in parallel (faster)
pytest tests/unit/ -n auto

# Verbose output with print statements
pytest -v -s tests/unit/
```

### Test File Structure

```
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_beaconing.py
│   ├── test_road_detection.py
│   └── api/
│       ├── test_tracks.py
│       └── test_positions.py
├── integration/
│   ├── test_database.py
│   └── test_api_flows.py
└── e2e/
    └── test_full_tracking.py
```

### Writing Good Unit Tests

```python
import pytest
from src.beaconing import calculate_beacon_interval

class TestSmartBeaconing:
    """Tests for smart beaconing algorithm."""
    
    def test_beacon_interval_at_rest(self):
        """Should use maximum interval when stationary."""
        interval = calculate_beacon_interval(speed_kmh=0, heading_change=0)
        assert interval == 1800  # 30 minutes max
    
    def test_beacon_interval_at_highway_speed(self):
        """Should use minimum interval at high speed."""
        interval = calculate_beacon_interval(speed_kmh=120, heading_change=0)
        assert interval == 60  # 1 minute min
    
    def test_beacon_on_turn(self):
        """Should beacon immediately on significant heading change."""
        interval = calculate_beacon_interval(speed_kmh=50, heading_change=45)
        assert interval == 0  # Immediate beacon
    
    @pytest.mark.parametrize("speed,expected", [
        (0, 1800),
        (30, 300),
        (60, 120),
        (100, 60),
    ])
    def test_beacon_interval_speed_scaling(self, speed, expected):
        """Interval should decrease as speed increases."""
        interval = calculate_beacon_interval(speed_kmh=speed, heading_change=0)
        assert interval == expected
```

### Test Fixtures (conftest.py)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    """Provide a clean database session for each test."""
    engine = create_engine("postgresql://test:test@localhost/test_db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_track_points():
    """Sample GPS track points for testing."""
    return [
        {"lat": 37.7749, "lon": -122.4194, "timestamp": "2024-01-01T10:00:00Z"},
        {"lat": 37.7750, "lon": -122.4195, "timestamp": "2024-01-01T10:00:05Z"},
        {"lat": 37.7755, "lon": -122.4200, "timestamp": "2024-01-01T10:00:10Z"},
    ]
```

### Coverage Requirements

```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# HTML report for detailed analysis
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

**CI will fail if coverage drops below 80%.**

---

## Code Review & Merging

### Opening a Pull Request

1. **Push your branch** to the remote repository
2. **Open a PR** on GitHub targeting `main`
3. **Fill out the PR template** completely:
   - Link to Jira ticket
   - Description of changes
   - Testing performed
   - Screenshots (if UI changes)
4. **Request reviewers** from your subteam

### PR Title Format

```
[CARP-123] Brief description of the change
```

### PR Checklist (Must Complete Before Review)

- [ ] Code follows project style guidelines
- [ ] Unit tests added/updated
- [ ] All tests pass locally (`pytest`)
- [ ] Coverage meets 80% threshold
- [ ] API documentation updated (if applicable)
- [ ] No secrets or credentials committed
- [ ] Branch is up-to-date with `main`

### Code Review Guidelines

**As an Author:**
- Keep PRs small and focused (< 400 lines ideal)
- Respond to feedback within 24 hours
- Don't take feedback personally—we're improving the code

**As a Reviewer:**
- Review within 24 hours of being requested
- Be constructive and specific
- Approve when ready, request changes if blocking issues exist
- Use GitHub's suggestion feature for small fixes

### Merging Requirements

A PR can be merged when:

1. ✅ At least **1 approval** from a teammate
2. ✅ All **CI checks pass** (tests, linting, coverage)
3. ✅ No **merge conflicts**
4. ✅ Branch is **up-to-date with main**

### Merge Strategy

We use **Squash and Merge** for all PRs:
- Creates a single commit on main
- Keeps history clean
- Commit message includes PR number

```
[CARP-123] Implement smart beaconing algorithm (#45)
```

### Post-Merge Cleanup

```bash
# After your PR is merged
git checkout main
git pull origin main

# Delete local feature branch
git branch -d dev/be/CARP-123-smart-beaconing

# Delete remote feature branch (if not auto-deleted)
git push origin --delete dev/be/CARP-123-smart-beaconing
```

---

## Quick Reference

### Daily Commands

```bash
# Morning setup
git checkout main && git pull && docker compose up -d

# Create feature branch
git checkout -b dev/be/CARP-XXX-feature-name

# Run tests before pushing
pytest tests/unit/ && git push

# End of day
docker compose down
```

### Useful Aliases (add to ~/.zshrc)

```bash
alias dc="docker compose"
alias dcu="docker compose up -d"
alias dcd="docker compose down"
alias dcl="docker compose logs -f"
alias gp="git pull origin main"
alias gcm="git checkout main"
```

---

## Getting Help

- **Discord Channels:** #backend, #frontend, #embedded, #infra, #general
- **Blocker Protocol:** Post in Discord, @ team lead if urgent
- **Documentation:** Check `/AI_Slop_MDs/` for architecture docs

---

*Last updated: February 2026*
