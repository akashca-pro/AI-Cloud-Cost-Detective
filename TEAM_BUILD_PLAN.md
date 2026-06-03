# Team Build Plan — AI Cloud Cost Detective

**Contributors:** [akash-ca](https://github.com/akashca-pro) · **devanarayan**

This document is the **single source of truth** for who builds what, in what order, and what is done.  
Each person **must update the [Progress Tracker](#progress-tracker)** when they start, finish, or review a work package (WP).

> **Repo:** https://github.com/akashca-pro/AI-Cloud-Cost-Detective.git

---

## How to use this file

### When you **start** a WP
1. Update the tracker: set **Status** → `In Progress`, fill **Lead**, **Branch**, **Started** date.
2. Commit on your feature branch: `docs: start WP# — <your name>` (include this file in the commit).

### When you **open a PR**
1. Update **PR link** in the tracker.
2. Tag your reviewer in GitHub and ping them in chat.

### When your reviewer **approves**
1. Reviewer updates **Review** column → `Approved`.
2. Lead merges PR to `develop`, then updates **Status** → `Merged`, **Merged** date, and **Notes** (one line on what shipped).

### When you **review** someone else's WP
1. Pull their branch locally and run their test steps.
2. Update **Review** → `Approved` or `Changes requested` with a short note in **Notes**.

### Commit message format for tracker updates
```text
docs: update TEAM_BUILD_PLAN — WP2 merged (devanarayan)
```

---

## Git workflow (both people)

| Branch | Purpose |
|--------|---------|
| `planning` | Docs, specs, this file |
| `develop` | All feature PRs merge here |
| `main` | Stable releases only |
| `feature/*` | One branch per WP |

**Rules**
- Always branch from latest `develop`: `git checkout develop && git pull && git checkout -b feature/wpX-...`
- Open PR: `feature/wpX-...` → `develop` (never direct push to `develop` or `main`)
- Every PR needs **one approval** from the other person
- Never commit `.env` — only update `.env.example`
- After a WP merges, both run: `git checkout develop && git pull origin develop`
- Do not add vendor attribution footers (e.g. `Co-authored-by`, "Made with …") to commits or PR descriptions

---

## Responsibility split (equal)

Each person **leads 3 WPs**, **reviews 3 WPs**, and **co-owns WP7**.

| Person | Leads | Reviews |
|--------|-------|---------|
| **akash-ca** | WP1, WP3, WP5 (+ WP6 ProgressTracker) | WP2, WP4, WP6 |
| **devanarayan** | WP2, WP4 (frontend), WP6 (backend WS) | WP1, WP3, WP5 |
| **Both** | WP7 | each other |

---

## Build order

Do **not** skip ahead. Wait for the previous WP to merge to `develop` unless noted.

```
WP1 → WP2 → WP3 → WP4 → WP5 → WP6 → WP7 → develop → main
```

---

## Progress Tracker

> **Update this table after every status change.**

| WP | Name | Status | Lead | Reviewer | Branch | PR | Started | Merged | Review | Notes |
|----|------|--------|------|----------|--------|-----|---------|--------|--------|-------|
| WP1 | AWS discovery + rules | `In Review` | akash-ca | devanarayan | `feature/wp1-resource-discovery` | [#3](https://github.com/akashca-pro/AI-Cloud-Cost-Detective/pull/3) | 2026-06-03 | — | — | Backend-only PR; awaiting devanarayan review |
| WP2 | OpenAI enrichment | `Not Started` | devanarayan | akash-ca | `feature/wp2-ai-enrichment` | — | — | — | — | Blocked until WP1 merged |
| WP3 | Database + history | `Not Started` | akash-ca | devanarayan | `feature/wp3-database-history` | — | — | — | — | Blocked until WP2 merged |
| WP4 | Auth full stack | `Not Started` | devanarayan (FE) / akash-ca (BE) | each other | `feature/wp4-auth-fullstack` | — | — | — | — | Blocked until WP3 merged |
| WP5 | Frontend pages | `Not Started` | devanarayan (History/Nav) / akash-ca (Dashboard/Report) | each other | `feature/wp5-frontend-pages` | — | — | — | — | Blocked until WP4 merged |
| WP6 | WebSocket progress | `Not Started` | devanarayan (BE WS) / akash-ca (ProgressTracker) | each other | `feature/wp6-websocket-progress` | — | — | — | — | Blocked until WP5 merged |
| WP7 | E2E integration | `Not Started` | Both | each other | `feature/wp7-integration-e2e` | — | — | — | — | Blocked until WP6 merged |

**Status values:** `Not Started` · `In Progress` · `In Review` · `Changes Requested` · `Merged`

---

# Work Packages — Step by Step

---

## WP1 — AWS discovery + rule-based detection

| | |
|--|--|
| **Lead** | akash-ca |
| **Reviewer** | devanarayan |
| **Branch** | `feature/wp1-resource-discovery` |
| **Reference** | `README.md` (planning), `backend/` structure |

### Goal
FastAPI backend discovers AWS resources via **boto3** and runs **deterministic FinOps rules**.

### Deliverables
- [ ] `backend/main.py` — `GET /api/health`, `GET /api/aws/regions`, `POST /api/analyze`
- [ ] `backend/scanners/` — EC2, RDS, S3, ELB, EBS
- [ ] `backend/detection/finops_detectors.py` — rule-based findings
- [ ] `backend/services/aws_discovery_service.py` — orchestration
- [ ] `backend/requirements.txt` — fastapi, uvicorn, boto3, pydantic
- [ ] PR merged to `develop`

### akash-ca — steps
1. `git checkout develop && git pull`
2. `git checkout -b feature/wp1-resource-discovery` *(already in progress)*
3. Implement backend (see deliverables above)
4. Test locally:
   ```bash
   cd backend && pip install -r requirements.txt && uvicorn main:app --reload
   curl http://localhost:8000/api/health
   curl http://localhost:8000/api/aws/regions
   curl -X POST http://localhost:8000/api/analyze -H "Content-Type: application/json" \
     -d '{"regions":["us-east-1"],"services":["ec2"],"tags":{}}'
   ```
5. Commit, push, open PR → `develop`
6. Update **Progress Tracker** → `In Review`, add PR link
7. Ping devanarayan to review

### devanarayan — steps
1. Wait for PR link from akash-ca
2. `git fetch origin && git checkout feature/wp1-resource-discovery`
3. Run the same curl tests with AWS credentials configured
4. Approve PR or request changes on GitHub
5. Update tracker **Review** column
6. After merge: `git checkout develop && git pull` — then start WP2

### Handoff to WP2
Share the `POST /api/analyze` response shape (`resources`, `findings`, `findings_summary`) with devanarayan.

---

## WP2 — OpenAI enrichment

| | |
|--|--|
| **Lead** | devanarayan |
| **Reviewer** | akash-ca |
| **Branch** | `feature/wp2-ai-enrichment` |

### Goal
OpenAI **enriches** rule-based findings — does not replace `FinOpsDetector`.

### Deliverables
- [ ] `backend/ai_analyzer.py` — takes `AnalyzeResponse`, returns AI summary + savings + AWS CLI fixes
- [ ] Wire into `POST /api/analyze` after `FinOpsDetector`
- [ ] `OPENAI_API_KEY` in `.env.example`
- [ ] `openai`, `python-dotenv` in `requirements.txt`
- [ ] PR merged to `develop`

### devanarayan — steps
1. Confirm WP1 merged; `git checkout develop && git pull`
2. `git checkout -b feature/wp2-ai-enrichment`
3. Read `backend/models/responses.py` and `backend/detection/finops_detectors.py`
4. Implement `ai_analyzer.py` — input: resources + findings; output: summary, estimated savings, fix commands per finding
5. Test with a real OpenAI key locally
6. Open PR → `develop`, update tracker, ping akash-ca

### akash-ca — steps
1. Review PR — verify AI runs **after** rule detection, not instead of it
2. Test locally with your OpenAI key
3. Approve or request changes; update tracker
4. After merge, start WP3

---

## WP3 — Database + analysis history

| | |
|--|--|
| **Lead** | akash-ca |
| **Reviewer** | devanarayan |
| **Branch** | `feature/wp3-database-history` |

### Goal
Persist analyses in **Amazon RDS PostgreSQL**.

### Deliverables
- [ ] `backend/db.py` — connection, `users` + `analyses` tables, save/query helpers
- [ ] `DATABASE_URL` in `.env.example`
- [ ] Store full analysis result after `POST /api/analyze` completes
- [ ] `GET /api/history` — devanarayan implements endpoint using akash's `db.py` helpers
- [ ] PR merged to `develop`

### akash-ca — steps
1. `git checkout develop && git pull`
2. `git checkout -b feature/wp3-database-history`
3. Implement `db.py` and table creation on startup
4. Wire save-after-analyze in `main.py` / service layer
5. Document `db.py` public functions for devanarayan
6. Open PR, update tracker, ping devanarayan

### devanarayan — steps
1. Add `GET /api/history` on same branch (commit to akash's branch or paired PR)
2. Test with local/RDS `DATABASE_URL`
3. Review akash's `db.py`; approve PR; update tracker

---

## WP4 — Auth (full stack)

| | |
|--|--|
| **Lead** | devanarayan (frontend) · akash-ca (backend) |
| **Reviewer** | each other |
| **Branch** | `feature/wp4-auth-fullstack` |

### Goal
Signup/login with JWT; credentials in RDS `users` table.

### Deliverables

**akash-ca (backend)**
- [ ] `POST /api/auth/signup` — bcrypt hash → JWT
- [ ] `POST /api/auth/login` — validate → JWT
- [ ] `JWT_SECRET` in `.env.example`
- [ ] `PyJWT`, `bcrypt` in `requirements.txt`

**devanarayan (frontend)**
- [ ] Scaffold `frontend/` — Vite + React + TypeScript + Tailwind (dark theme)
- [ ] `Login.tsx`, `Signup.tsx`
- [ ] JWT in `localStorage`; `Authorization: Bearer` on API calls
- [ ] Redirect to login if unauthenticated

### Steps (both)
1. Agree on API contract before coding:
   ```json
   POST /api/auth/signup  { "email": "...", "password": "..." }
   → { "token": "..." }
   ```
2. Branch from `develop`; both commit to `feature/wp4-auth-fullstack`
3. Test signup → login → token returned
4. One PR → `develop`; both review; update tracker

---

## WP5 — Frontend pages

| | |
|--|--|
| **Lead** | akash-ca (Dashboard, Report) · devanarayan (History, Navbar, routing) |
| **Reviewer** | each other |
| **Branch** | `feature/wp5-frontend-pages` |

### Goal
Core UI pages wired to mock or real API.

### Deliverables

**akash-ca**
- [ ] `Dashboard.tsx` — region/service/tag picker, Run Analysis button
- [ ] `Report.tsx` — findings, severity badges, copyable fix commands

**devanarayan**
- [ ] `History.tsx` — past analyses list
- [ ] `Navbar.tsx` + routing in `App.tsx`

### Steps (both)
1. Branch from `develop`
2. Build your pages; use mock data if backend endpoints not ready
3. One PR; cross-review UI; update tracker

---

## WP6 — WebSocket progress

| | |
|--|--|
| **Lead** | devanarayan (backend WS) · akash-ca (ProgressTracker) |
| **Reviewer** | each other |
| **Branch** | `feature/wp6-websocket-progress` |

### Goal
Live progress during analysis.

### Deliverables

**devanarayan**
- [ ] `ws://localhost:8000/ws/progress/{analysis_id}`
- [ ] Progress events during analyze: fetching → scanning → AI → storing → complete

**akash-ca**
- [ ] `ProgressTracker.tsx` — animated step list
- [ ] Connect from `Dashboard.tsx`

### Steps (both)
1. **Agree first** on message format, e.g. `{ "message": "Scanning resources..." }`
2. devanarayan implements WebSocket backend
3. akash-ca implements frontend component
4. Test together locally; one PR; update tracker

---

## WP7 — End-to-end integration

| | |
|--|--|
| **Lead** | Both |
| **Reviewer** | each other |
| **Branch** | `feature/wp7-integration-e2e` |

### Goal
Full app flow works end to end.

### Deliverables

**akash-ca**
- [ ] JWT middleware on protected routes: `/api/analyze`, `/api/history`, `/api/aws/regions`
- [ ] Backend E2E test checklist

**devanarayan**
- [ ] Central API client with auth headers
- [ ] Wire Dashboard, Report, History to real APIs + WebSocket

### E2E test checklist (both must pass)
- [ ] Signup
- [ ] Login
- [ ] Select regions / services / tags
- [ ] Run analysis
- [ ] See live WebSocket progress
- [ ] View report with findings + AI summary
- [ ] View history; open past report

### Steps
1. Branch from `develop`
2. Complete your half; pair-test full flow
3. Both approve PR; merge to `develop`
4. Merge `develop` → `main` when stable
5. Update tracker — all WPs `Merged`

---

## Quick reference — who does what

| WP | akash-ca | devanarayan |
|----|----------|-------------|
| WP1 | Build discovery backend | Review + test |
| WP2 | Review + test | Build `ai_analyzer.py` |
| WP3 | Build `db.py` | Add `/api/history` + review |
| WP4 | Backend auth endpoints | Login/Signup UI |
| WP5 | Dashboard + Report | History + Navbar + routing |
| WP6 | `ProgressTracker.tsx` | WebSocket backend |
| WP7 | JWT guards + BE tests | API client + FE wiring |

---

## Development prompts

When starting a WP in your editor, say:

```text
Implement WP# for AI Cloud Cost Detective. I am [akash-ca | devanarayan].
Read TEAM_BUILD_PLAN.md and follow my role for this WP.
Branch from develop. Update TEAM_BUILD_PLAN.md progress tracker when done.
```

---

## Changelog

| Date | Person | Update |
|------|--------|--------|
| 2026-06-03 | akash-ca | Created TEAM_BUILD_PLAN.md; WP1 in progress |
| 2026-06-03 | akash-ca | Removed Cursor branding from team build plan |
| 2026-06-03 | akash-ca | WP1 → In Review; PR #3 opened |
