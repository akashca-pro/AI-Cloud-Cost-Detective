## AI Cloud Cost Detective - Request Flow

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
