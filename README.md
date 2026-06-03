# AI Cloud Cost Detective

An AI-powered AWS FinOps tool that discovers cloud resources across regions, runs deterministic cost checks, and (planned) enriches findings with OpenAI summaries and actionable AWS CLI fixes.

## Current Status

| Area | Status |
|------|--------|
| AWS discovery (boto3) | ✅ Implemented |
| Rule-based FinOps detection | ✅ Implemented |
| OpenAI enrichment | 🔜 Planned |
| Auth (JWT) | 🔜 Planned |
| Database (Amazon RDS PostgreSQL) | 🔜 Planned |
| WebSocket progress | 🔜 Planned |
| React frontend | 🔜 Planned |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React (Vite + TypeScript + Tailwind) — *planned* |
| Backend | Python (FastAPI) |
| AWS integration | **boto3** (EC2, RDS, S3, ELB, EBS, CloudWatch, STS) |
| Detection | Deterministic rule engine (`FinOpsDetector`) |
| AI enrichment | OpenAI API — *planned* |
| Auth | Custom JWT (bcrypt + PyJWT) — *planned* |
| Database | Amazon RDS for PostgreSQL — *planned* |
| Live updates | FastAPI WebSocket — *planned* |

## Architecture

```
                              ┌──────────────┐
                              │     USER     │
                              └──────┬───────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │  REACT FRONTEND   │  (planned)
                           └────────┬──────────┘
                                    │
                                    ▼
                           ┌───────────────────┐
                           │  PYTHON BACKEND   │
                           │    (FastAPI)      │
                           │                   │
                           │  · JWT Auth       │  (planned)
                           │  · Discovery      │  ✅
                           │  · Rule detection │  ✅
                           └───┬───────┬───┬───┘
                               │       │   │
                ┌──────────────┘       │   └──────────────┐
                ▼                      ▼                  ▼
         ┌─────────────┐     ┌──────────────┐    ┌──────────────┐
         │   BOTO3     │     │   FASTAPI    │    │   OPENAI     │
         │  AWS APIs   │     │  WEBSOCKET   │    │    API       │
         │             │     │  (planned)   │    │  (planned)   │
         │ EC2/RDS/S3  │     └──────┬───────┘    │ Enrich       │
         │ ELB/EBS/CW  │            │            │ findings     │
         └──────┬──────┘            │            └──────┬───────┘
                │                   │                     │
                ▼                   ▼                     │
         ┌─────────────┐   ┌───────────────┐            │
         │    AWS      │   │    REACT      │            │
         │  Account    │   │  Progress UI  │            │
         │  (regions,  │   │  (planned)    │            │
         │   tags)     │   └───────────────┘            │
         └─────────────┘                                  ▼
                                                 ┌──────────────┐
                                                 │   AMAZON     │
                                                 │ RDS POSTGRES │  (planned)
                                                 │ · users      │
                                                 │ · analyses   │
                                                 └──────────────┘
```

## Request Flow (target end-to-end)

```
①  User ──► React ──► FastAPI Auth ──► JWT (Amazon RDS PostgreSQL)     [planned]

②  User selects regions, services, and tag filters ──► Python Backend

③  Python ──► boto3 ──► Discovers EC2, RDS, S3, ELB, EBS resources   [✅ done]

④  Python ──► FinOpsDetector ──► Rule-based findings                  [✅ done]

⑤  Python ──► OpenAI API ──► Summary, savings, AWS CLI fix commands   [planned]

⑥  Python ──► FastAPI WebSocket ──► React (live progress)             [planned]

⑦  Python ──► Amazon RDS PostgreSQL ──► Stores analysis history       [planned]

⑧  React ◄── Final report with findings, AI summary, and fixes        [planned]
```

## Backend Structure

```
backend/
├── main.py                          # FastAPI routes
├── core/
│   ├── exceptions.py                # AWS error types
│   ├── session.py                   # boto3 session helpers
│   └── cloudwatch.py                # CPU/utilization metrics
├── models/
│   ├── requests.py                  # AnalyzeRequest
│   ├── responses.py                 # AnalyzeResponse, WorkloadSummary
│   └── resources.py                 # NormalizedResource, Finding
├── scanners/
│   ├── ec2_scanner.py
│   ├── rds_scanner.py
│   ├── s3_scanner.py
│   ├── elb_scanner.py
│   └── ebs_scanner.py
├── detection/
│   └── finops_detectors.py          # Rule-based cost findings
└── services/
    └── aws_discovery_service.py     # Orchestration
```

## API (implemented)

### `GET /api/health`

Returns service health and cloud provider.

### `GET /api/aws/regions`

Lists enabled AWS regions for the configured account.

### `POST /api/analyze`

Discover resources and run deterministic FinOps checks.

**Request body:**

```json
{
  "regions": ["us-east-1", "us-west-2"],
  "services": ["ec2", "rds", "s3", "elb", "ebs"],
  "tags": { "Environment": "prod", "Project": "payments" }
}
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `regions` | No | all enabled regions | AWS regions to scan |
| `services` | No | all five services | `ec2`, `rds`, `s3`, `elb`, `ebs` |
| `tags` | No | `{}` | Tag filter (AND semantics) |

**Response includes:** `resources`, `workloads`, `findings`, `findings_summary`, `account_id`, `regions_scanned`, `services_scanned`.

## What It Detects Today (rule-based)

| Service | Finding | Severity |
|---------|---------|----------|
| EC2 | Low CPU utilization (<10% over 7 days) | medium |
| EC2 | Stopped instance (EBS may still bill) | low |
| EBS | Unattached volume | high |
| ELB | No healthy targets | medium |
| S3 | Missing lifecycle policy | medium |
| RDS | Large instance in dev/test/staging | medium |

OpenAI will later add narrative summaries, estimated savings, and copyable AWS CLI remediation commands.

## Prerequisites

**Required now (backend):**

- Python 3.10+
- AWS credentials configured (env vars, `~/.aws/credentials`, or IAM role)
- IAM permissions to describe EC2, RDS, S3, ELB, EBS, CloudWatch, STS, and list regions

**Required later (full app):**

- Amazon RDS for PostgreSQL
- OpenAI API key
- Node.js 18+

## How to Run

### Backend (available now)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Example requests:**

```bash
curl http://localhost:8000/api/health

curl http://localhost:8000/api/aws/regions

curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"regions":["us-east-1"],"services":["ec2","ebs"],"tags":{"Environment":"prod"}}'
```

Interactive docs: http://localhost:8000/docs

### Frontend (not yet implemented)

```bash
cd frontend
npm install
npm run dev
```

## Team & Git Workflow

**Contributors:** akash-ca · devanarayan

| Branch | Purpose |
|--------|---------|
| `planning` | Docs and specs |
| `develop` | Integration branch |
| `main` | Stable releases |
| `feature/*` | Feature work |

## Team Responsibilities

Work is split equally: each person **leads 3 work packages**, **reviews 3**, and **co-owns integration**.

| WP | Branch | Lead | Reviewer | Scope |
|----|--------|------|----------|-------|
| **WP1** AWS discovery + rules | `feature/wp1-aws-discovery` | **akash-ca** ✅ | devanarayan | boto3 scanners, `FinOpsDetector`, `/api/analyze`, `/api/aws/regions` |
| **WP2** OpenAI enrichment | `feature/wp2-ai-enrichment` | **devanarayan** | akash-ca | `ai_analyzer.py` — summarize findings, estimate savings, AWS CLI fixes |
| **WP3** Database + history | `feature/wp3-database-history` | **akash-ca** | devanarayan | `db.py`, persist analyses; devanarayan adds `GET /api/history` |
| **WP4** Auth (full stack) | `feature/wp4-auth-fullstack` | **devanarayan** (frontend) / **akash-ca** (backend) | each other | Signup/Login UI + JWT endpoints |
| **WP5** Frontend pages | `feature/wp5-frontend-pages` | **devanarayan** (History, Navbar, routing) / **akash-ca** (Analyze form, Report) | each other | Region/service/tag picker, findings report UI |
| **WP6** WebSocket progress | `feature/wp6-websocket-progress` | **devanarayan** (backend WS) | akash-ca | **akash-ca:** `ProgressTracker.tsx` |
| **WP7** E2E integration | `feature/wp7-integration-e2e` | **Both** | each other | JWT guards, API client, full flow test |

**Rules:** branch from `develop` · PR to `develop` · peer review required · never commit `.env`

## How It Works (full app — target)

1. User signs up / logs in (JWT stored in Amazon RDS PostgreSQL)
2. User selects regions, services, and optional tag filters in the Dashboard
3. Backend discovers AWS resources via boto3 scanners
4. Rule engine produces deterministic FinOps findings
5. OpenAI enriches results with summary, savings estimate, and AWS CLI fix commands
6. Progress streams to the UI via WebSocket
7. Results are stored in RDS; History page shows past analyses
8. Report page displays findings, AI summary, and copyable remediation commands
