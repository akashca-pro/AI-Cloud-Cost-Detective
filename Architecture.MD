## AI Cloud Cost Detective - Architecture

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
                                                 └──────┬───────┘
                                                        │
                                                        ▼
                                                 ┌───────────────┐
                                                 │    REACT      │
                                                 │ (Final Report │
                                                 │  + Suggestions│
                                                 │  + Fixes)     │
                                                 └───────────────┘
```
