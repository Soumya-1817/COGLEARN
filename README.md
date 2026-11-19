# COGLEARN Platform

**COGLEARN** is an Intelligent Learning and Cognitive Risk Management Platform that models academic workload demand, student processing capacity, and real-time cognitive state transitions.

---

## Architecture Overview

- **Backend Framework**: FastAPI (Python 3.11) with Async SQLAlchemy 2.0 and Pydantic v2.
- **Database**: PostgreSQL 15 with Row-Level Security (RLS) and session-local multi-tenant isolation (`SET LOCAL app.current_tenant_id`).
- **Distributed Task Queue**: Celery 5.4 with Redis 7 broker and Celery Beat scheduler.
- **Authentication**: Asymmetric RS256 JWT access tokens with rotating Refresh Tokens (family compromise detection) and HTTP-only cookie support.
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS with TanStack Query and Zustand.

---

## The Four Cognitive Mathematical Models

### Model 1: Bayesian Capacity Estimation ($\mu$)
- Models student cognitive throughput capacity as a random variable $\mu \sim \text{Gamma}(\alpha, \beta)$.
- Uses conjugate Poisson-Gamma updates on empirical daily activity interactions.
- Prior distribution: $\mu \sim \text{Gamma}(\alpha_0, \beta_0)$ where $\alpha_0 = 10.0, \beta_0 = 2.0$ (**PROVISIONAL**).
- Computes posterior mean $\mathbb{E}[\mu]$, variance $\text{Var}(\mu)$, and 95% Credible Intervals.

### Model 2: M/M/1 Queueing Network Analysis
- Models academic workload processing as an $M/M/1$ queue:
  - Arrival rate: $\lambda$ (workload demand from Model 3)
  - Service rate: $\mu$ (mean capacity from Model 1)
  - Utilization ratio: $\rho = \frac{\lambda}{\mu}$
  - Expected tasks in system: $L = \frac{\rho}{1 - \rho} = \frac{\lambda}{\mu - \lambda}$ (for $\rho < 1.0$)
  - Expected response/wait time: $W = \frac{L}{\lambda} = \frac{1}{\mu - \lambda}$ (Little's Law)
- Identifies queue instability ($\rho \ge 1.0$) where student demand outpaces capacity.

### Model 3: ICAP-Weighted Workload ($\lambda$)
- Telemetry activity aggregator weighting user actions according to the Chi & Wylie ICAP framework:
  - **Passive** ($w = 0.5$, video, view resource) (**PROVISIONAL**)
  - **Active** ($w = 1.0$, navigate, read, test attempts) (**PROVISIONAL**)
  - **Constructive** ($w = 1.8$, note-taking, assignment completion) (**PROVISIONAL**)
  - **Interactive** ($w = 2.5$, collaborative sessions, peer engagement) (**PROVISIONAL**)
- Causal 3-day moving average filter prevents lookahead bias.

### Model 4: Latent Cognitive State HMM & IORI
- 4 hidden states: **Underload**, **Flow**, **Overload**, **Fatigue**.
- Forward algorithm computes posterior state distributions $P(S_t \mid O_{1:t})$ based on the observation vector $O_t = [\rho_t, \text{ineffective\_ratio}_t, \text{overdue\_count}_t, \text{session\_time}_t]$.
- **Index of Overload and Risk of Ineffectiveness (IORI)**:
  $$\text{IORI}(t) = P(S_t = \text{Overload} \mid O_{1:t}) + P(S_t = \text{Fatigue} \mid O_{1:t})$$
- Risk classifications:
  - **Green** ($\text{IORI} < 0.35$): Normal / Safe (**PROVISIONAL**)
  - **Yellow** ($0.35 \le \text{IORI} < 0.65$): Attentive Caution (**PROVISIONAL**)
  - **Red** ($\text{IORI} \ge 0.65$): Acute Cognitive Overload Alert (**PROVISIONAL**)

> **Student Privacy Safeguard**:
> The `iori`, `hmm_probabilities`, $\alpha_{\text{post}}$, $\beta_{\text{post}}$, and mentor notes are strictly isolated to mentor and institutional administrative roles. Student-facing API endpoints never expose cognitive risk internals.

---

## Quickstart

### 1. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Generate RS256 RSA keys (or use default development fallback):
```bash
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
```

### 2. Launch Services with Docker Compose
```bash
make up
# Or: docker-compose up -d
```

### 3. Run Database Migrations
```bash
make migrate
# Or: docker-compose exec api alembic upgrade head
```

### 4. Access Platform
- **FastAPI Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Frontend Application**: http://localhost:5173
- **Celery Flower**: http://localhost:5555

---

## Project Structure

```
d:\COGLEARN\
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── alembic.ini           # Alembic configuration
│   ├── app/
│   │   ├── api/              # FastAPI routers and dependencies
│   │   │   ├── deps.py       # RBAC & Tenant dependency injection
│   │   │   └── v1/routers/   # Auth, Institutions, Users routers
│   │   ├── core/             # Configuration, DB session, Security
│   │   ├── models/           # 35 SQLAlchemy 2.0 declarative models
│   │   ├── schemas/          # Pydantic v2 validation schemas
│   │   └── worker/           # Celery application & beat scheduler
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/                  # React 18 + Vite frontend
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml        # Multi-container orchestration
├── Makefile                  # Developer workflow shortcuts
└── .env.example              # Configuration template
```
