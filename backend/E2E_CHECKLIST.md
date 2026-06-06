# Backend E2E Test Checklist (WP7)

Run with backend on `http://localhost:8000`, `DATABASE_URL` and `JWT_SECRET` set in `.env`.

## Auth

- [ ] `POST /api/auth/signup` with `{ "email", "password" }` → `200` + `{ "token" }`
- [ ] `POST /api/auth/login` with same credentials → `200` + `{ "token" }`
- [ ] Duplicate signup → `409`
- [ ] Wrong password on login → `401`

## JWT protection

Protected routes require `Authorization: Bearer <token>`:

- [ ] `GET /api/aws/regions` without token → `401`
- [ ] `POST /api/analyze` without token → `401`
- [ ] `GET /api/history` without token → `401`
- [ ] `GET /api/history/{id}` without token → `401`
- [ ] Expired or invalid token → `401`

Public routes (no JWT):

- [ ] `GET /api/health` → `200`
- [ ] `POST /api/auth/signup` / `POST /api/auth/login` → no Bearer required

## Analyze + persistence

```bash
export TOKEN="<jwt>"
export ANALYSIS_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"
```

- [ ] `POST /api/analyze` with token + body including `analysis_id` → `200` + findings
- [ ] Response `analysis_id` matches request
- [ ] Row saved in DB with authenticated `user_id` (not NULL)

## History scoping

- [ ] `GET /api/history` with user A token → only user A analyses
- [ ] User B cannot `GET /api/history/{user_a_analysis_id}` → `404`

## WebSocket progress (WP6)

- [ ] Connect `ws://localhost:8000/ws/progress/{analysis_id}` before analyze
- [ ] Receive events: `fetching` → `scanning` → `ai` → `storing` → `complete`
- [ ] Payload shape: `{ "analysis_id", "step", "status", "message" }`

## Full stack (with frontend)

Pair with frontend E2E checklist in `TEAM_BUILD_PLAN.md` WP7:

- [ ] Signup → login → dashboard loads regions
- [ ] Run analysis → live progress → report
- [ ] History lists scans → open past report
