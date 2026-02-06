# Carputer Team Charter

## Mission
Build GPS tracking carputer with new road detection, APRS, and offline maps

## Team Structure
- Backend Team (3): [Names] - Go + C++
- Frontend Team (2): [Names] - TypeScript + Svelte  
- Embedded Team (2): [Names] - Rust + C
- Infrastructure (1): [Names] - Python/DevOps

## Communication
- Daily: Slack async updates
- Tues/Thurs: 30 min standup
- Friday: Sprint review (if in sprint)

## Definition of Done
- Code reviewed by 1+ teammate
- Tests pass in CI
- Documented (README + inline comments)
- Deployed to dev environment
```

---

## Week 3, Day 1 (Monday) - Team Kickoff Meeting

### **Agenda (2 hours)**

**Part 1: Project Overview (30 min)**

1. **Welcome & Introductions** (10 min)
   - Name, background, what excites you about this project
   - Share your dev environment (Arch+i3+Neovim, others share theirs)

2. **Project Vision** (10 min)
   - Show instructor requirements
   - Demo existing GPS tracking apps (show gaps)
   - Explain "new road detection" concept
   - Show dash cam team's project (how we collaborate)

3. **Architecture Walkthrough** (10 min)
   - Show architecture diagram
   - Explain technology choices (Go, Svelte, Rust, C++)
   - Explain why polyglot (right tool for each job)

**Part 2: Team Organization (45 min)**

4. **Skills Assessment** (15 min)
   - Quick poll: Who's strongest in what language?
   - Who has experience with: databases, embedded, web dev, DevOps?
   - Who WANTS to work on what?

5. **Team Assignments** (20 min)
   - Announce teams (based on skills + interests)
   - Explain each team's charter
   - Clarify: Everyone can contribute anywhere, but you "own" your domain

6. **Communication Norms** (10 min)
   - Slack channels: #general, #backend, #frontend, #embedded, #infra
   - Standups: Async daily updates, sync Tues/Thurs 30 min
   - Code reviews: Required, 1 approval minimum
   - Blocker protocol: Post in Slack, @ team lead if urgent

**Part 3: Sprint 0 Planning (45 min)**

7. **Sprint 0 Goals** (10 min)
   - **Theme**: "Walking Skeleton" - GPS → Database → Map
   - **Duration**: Weeks 3-4 (2 weeks)
   - **Demo**: GPS coordinates flow end-to-end

8. **User Stories Breakdown** (20 min)
   - Story 1: As a user, I can see my current GPS position on a map
   - Story 2: As a user, GPS points are saved to database
   - Story 3: As a developer, I can run the system locally with Docker
   - Story 4: As a team, we have CI/CD running tests

9. **Task Assignment** (15 min)
   - Break stories into tasks
   - Assign to teams
   - Identify dependencies

---

## Sprint 0: Detailed Task Breakdown

### **Backend Team (You + 2 devs)**

**Week 3:**
- [ ] **Task 1.1**: Set up Go project structure (go.mod, folder layout)
  - Owner: [Dev 1]
  - Deliverable: `carputer/backend/go/` with main.go, can run locally
  
- [ ] **Task 1.2**: PostgreSQL + PostGIS Docker setup
  - Owner: [Dev 2]
  - Deliverable: docker-compose.yml, database initializes with schema
  
- [ ] **Task 1.3**: Database schema v1 (tracks, points tables)
  - Owner: You
  - Deliverable: SQL migration files, PostGIS extensions enabled

**Week 4:**
- [ ] **Task 1.4**: REST API endpoint: `POST /api/gps-points` (store GPS point)
  - Owner: [Dev 1]
  - Deliverable: Can curl endpoint, data appears in PostgreSQL
  
- [ ] **Task 1.5**: REST API endpoint: `GET /api/gps-points` (retrieve points)
  - Owner: [Dev 1]
  - Deliverable: Frontend can fetch and display points
  
- [ ] **Task 1.6**: WebSocket server (real-time GPS updates)
  - Owner: [Dev 2]
  - Deliverable: Frontend connects, receives live updates

---

### **Frontend Team (2 devs)**

**Week 3:**
- [ ] **Task 2.1**: Svelte + Vite project setup
  - Owner: [Dev 3]
  - Deliverable: `npm run dev` works, shows "Hello World"
  
- [ ] **Task 2.2**: Leaflet.js map integration
  - Owner: [Dev 3]
  - Deliverable: Map displays OpenStreetMap, centered on Portland

**Week 4:**
- [ ] **Task 2.3**: Display current GPS position as marker on map
  - Owner: [Dev 3]
  - Deliverable: Marker moves when GPS updates
  
- [ ] **Task 2.4**: Fetch historical GPS points from API, display as track
  - Owner: [Dev 4]
  - Deliverable: Polyline shows path on map
  
- [ ] **Task 2.5**: WebSocket connection for live updates
  - Owner: [Dev 4]
  - Deliverable: Map updates in real-time without refresh

---

### **Embedded Team (2 devs)**

**Week 3:**
- [ ] **Task 3.1**: Rust project setup (Cargo.toml, folder structure)
  - Owner: [Dev 5]
  - Deliverable: `cargo run` works
  
- [ ] **Task 3.2**: GPS module hardware testing (if available)
  - Owner: [Dev 5]
  - Deliverable: Can read NMEA sentences from GPS
  
- [ ] **Task 3.3**: gpsd installation and configuration
  - Owner: [Dev 6]
  - Deliverable: gpsd running, `cgps` shows position

**Week 4:**
- [ ] **Task 3.4**: Rust GPS reader (connects to gpsd, parses data)
  - Owner: [Dev 5]
  - Deliverable: Rust program prints lat/lon to console
  
- [ ] **Task 3.5**: IPC to Go backend (Unix socket or UDP)
  - Owner: [Dev 6]
  - Deliverable: Rust sends GPS data, Go receives and logs it
  
- [ ] **Task 3.6**: Systemd service for auto-start
  - Owner: [Dev 6]
  - Deliverable: Service starts on boot, restarts on crash

---

### **Infrastructure Team (1 dev)**

**Week 3:**
- [ ] **Task 4.1**: GitHub repo setup (structure, README, .gitignore)
  - Owner: [Dev 7]
  - Deliverable: Team can clone and contribute
  
- [ ] **Task 4.2**: Docker dev environment (Go, PostgreSQL, maybe Rust)
  - Owner: [Dev 7]
  - Deliverable: `docker-compose up` starts everything
  
- [ ] **Task 4.3**: GitHub Actions basic CI (run tests, lint)
  - Owner: [Dev 7]
  - Deliverable: PR checks run automatically

**Week 4:**
- [ ] **Task 4.4**: Pi 4 setup documentation
  - Owner: [Dev 7]
  - Deliverable: Step-by-step guide to flash SD card, install deps
  
- [ ] **Task 4.5**: Deployment script (copy binaries to Pi)
  - Owner: [Dev 7]
  - Deliverable: One command deploys latest code to Pi

---

## Repository Structure (Create This Week 3)
```
carputer/
├── .github/
│   └── workflows/
│       ├── backend.yml       # Go CI
│       ├── frontend.yml      # Svelte CI
│       └── embedded.yml      # Rust CI
│
├── backend/
│   ├── go/                   # Go backend
│   │   ├── cmd/
│   │   │   └── server/
│   │   │       └── main.go
│   │   ├── internal/
│   │   │   ├── api/          # REST handlers
│   │   │   ├── db/           # Database layer
│   │   │   └── ws/           # WebSocket
│   │   ├── go.mod
│   │   └── go.sum
│   │
│   └── cpp/                  # C++ spatial processing (later)
│       ├── src/
│       ├── include/
│       └── CMakeLists.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Map.svelte
│   │   ├── lib/
│   │   │   └── api.ts        # Backend API client
│   │   ├── App.svelte
│   │   └── main.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── embedded/
│   ├── rust/
│   │   ├── src/
│   │   │   ├── gps/          # GPS reader
│   │   │   ├── ipc/          # Unix socket client
│   │   │   └── main.rs
│   │   └── Cargo.toml
│   │
│   └── c/                    # C hardware interfaces (later)
│       └── gps_interface.c
│
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile.go
│   │   └── Dockerfile.postgres
│   ├── scripts/
│   │   ├── deploy_to_pi.py
│   │   └── create_sd_image.py
│   └── systemd/
│       └── carputer.service
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md                # REST API documentation
│   └── SETUP.md              # Development setup
│
├── README.md
└── Makefile                  # Orchestrate builds
```

---

## Communication Plan

### **Daily (Async)**
**Slack Standup Template** (post by 10am):
```
Yesterday: [What I worked on]
Today: [What I'm working on]
Blockers: [Anything blocking me] or "None"


