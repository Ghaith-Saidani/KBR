# Knights of Bizertin Rise (KBR)

Official web platform for **Knights of Bizertin Rise (KBR)**, an esports organization based in Bizerte, Tunisia.

The project provides a modern full-stack platform for managing and presenting KBR's members, events, activities, news, communications, notifications, statistics, and AI-powered assistance.

---

## ðŸ“Œ Project Overview

KBR is designed as a modular, scalable web application combining:

* Public-facing esports organization website
* Member management
* Event management
* Activities and projects management
* News and articles management
* User authentication and accounts
* Role-based administration
* Contact management
* Notifications
* Statistics and monitoring
* AI-powered KBR assistant
* Database-backed contextual retrieval
* Automated testing
* Continuous Integration

The architecture is designed to evolve toward a larger data and AI platform including semantic search, RAG/LLM capabilities, Elasticsearch, behavioral analytics, Power BI, Docker-based deployment, and CI/CD.

---

# ðŸ—ï¸ Architecture

```text
                         KBR PLATFORM
                              â”‚
             â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
             â”‚                                 â”‚
        React Frontend                    FastAPI Backend
             â”‚                                 â”‚
     â”Œâ”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
     â”‚       â”‚        â”‚              â”‚         â”‚         â”‚
   Pages  Features    AI           APIs     Services     AI
     â”‚       â”‚        â”‚              â”‚         â”‚         â”‚
     â””â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”˜              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                               â”‚
                                          SQLAlchemy
                                               â”‚
                                          PostgreSQL
                                               â”‚
                              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                              â”‚                                â”‚
                         Application                    AI / Retrieval
                            Data                            Layer
```

The project follows a modular architecture separating presentation, API, business logic, persistence, and AI responsibilities.

---

# ðŸ› ï¸ Technology Stack

## Frontend

* React 19
* TypeScript
* Vite
* React Router
* TanStack Query
* Zustand
* Axios
* Tailwind CSS
* React Markdown

### Frontend testing

* Vitest
* Testing Library
* Playwright

---

## Backend

* Python 3.12
* FastAPI
* SQLAlchemy
* Pydantic
* Pydantic Settings
* PostgreSQL
* Alembic
* JWT authentication

---

## AI

The AI subsystem is implemented as a modular architecture rather than coupling the application directly to a single model provider.

```text
AI Request
    â”‚
    â–¼
AI Router
    â”‚
    â–¼
AI Service
    â”‚
    â”œâ”€â”€ Intent Classification
    â”‚
    â”œâ”€â”€ Context Retrieval
    â”‚
    â”œâ”€â”€ Context Formatting
    â”‚
    â–¼
Model Gateway
    â”‚
    â”œâ”€â”€ Gemini
    â””â”€â”€ Groq
    â”‚
    â–¼
AI Response
```

The current retrieval layer can retrieve relevant public KBR information from the application database before sending context to the model.

This architecture provides a foundation for future:

* Semantic search
* Embeddings
* Vector search
* RAG
* LLM-powered knowledge retrieval
* Advanced AI agents

---

# ðŸ” Authentication & Authorization

KBR implements authentication and role-based access control.

Supported roles include:

```text
member
staff
admin
```

Protected frontend routes use:

```text
ProtectedRoute
RoleRoute
```

Backend authorization protects administrative operations independently of frontend visibility.

---

# ðŸ‘¥ Members

The member management system supports:

* Public member listing
* Member profiles
* Member/user association
* Profile updates
* Administrative member management
* Member status management
* Slug-based public profiles

Member statuses include:

```text
ACTIVE
INACTIVE
ARCHIVED
```

---

# ðŸ“… Events

The platform provides both public event presentation and administrative event management.

Administrators/staff can:

* View events
* Create events
* Edit events
* Manage event information

Public users can access event listings and individual event detail pages.

---

# ðŸ“° News

KBR includes a complete news/content management section.

Features include:

* Public news listing
* News detail pages
* Administrative news management
* News creation
* News editing
* Slug-based news URLs

---

# ðŸš€ Activities

Activities and projects are managed through a dedicated module.

Features include:

* Public activity listing
* Activity detail pages
* Administrative activity management
* Activity creation
* Activity editing

---

# ðŸ”” Notifications

Authenticated users have access to a notification system through their personal account area.

---

# ðŸ“© Contact

The platform includes:

* Public contact form
* Backend contact processing
* Administrative contact management

---

# ðŸ“Š Statistics

KBR includes a statistics subsystem for monitoring application activity and presenting administrative metrics.

The statistics architecture provides a foundation for future behavioral analytics and business intelligence.

The planned evolution includes:

```text
User Activity
     â”‚
     â–¼
Event / Activity Logging
     â”‚
     â–¼
Data Processing
     â”‚
     â”œâ”€â”€ PostgreSQL
     â””â”€â”€ Elasticsearch
             â”‚
             â–¼
          Analytics
             â”‚
             â–¼
          Power BI
```

---

# ðŸ¤– AI Assistant

KBR includes an integrated AI assistant accessible from the frontend.

The assistant is designed specifically around KBR's own information rather than functioning as a generic chatbot.

Current architecture includes:

```text
Frontend AI Chat
       â”‚
       â–¼
POST /ai/chat
       â”‚
       â–¼
Intent Processing
       â”‚
       â–¼
KBR Context Retrieval
       â”‚
       â–¼
Context Formatting
       â”‚
       â–¼
Model Gateway
       â”‚
       â–¼
AI Provider
       â”‚
       â–¼
Response
```

The backend controls model/provider configuration, preventing the frontend from arbitrarily selecting AI providers or models.

---

# ðŸ—„ï¸ Database

PostgreSQL is the primary application database.

SQLAlchemy is used as the ORM and Alembic manages database migrations.

Current main domain entities include:

```text
User
Member
Event
Activity
News
Notification
Contact
```

Database migrations are version-controlled and executed through Alembic.

---

# ðŸ³ Docker

Docker Compose is currently used to provision the PostgreSQL development database.

Current infrastructure includes:

```text
Docker Compose
      â”‚
      â–¼
PostgreSQL 17
      â”‚
      â–¼
Persistent volume
```

The long-term architecture will extend Dockerization to the complete application:

```text
Docker Compose
â”œâ”€â”€ Frontend
â”œâ”€â”€ Backend
â”œâ”€â”€ PostgreSQL
â”œâ”€â”€ Elasticsearch
â””â”€â”€ Supporting services
```

---

# ðŸ”„ Continuous Integration

The project includes GitHub Actions CI.

The CI pipeline performs automated checks including:

```text
Push
 â”‚
 â–¼
GitHub Actions
 â”‚
 â”œâ”€â”€ PostgreSQL service
 â”œâ”€â”€ Python environment
 â”œâ”€â”€ Backend compilation
 â”œâ”€â”€ Alembic migrations
 â””â”€â”€ Pytest
```

The frontend also provides automated linting, testing, and production build checks.

---

# ðŸ§ª Testing

The project contains automated tests covering multiple layers of the application.

## Backend

Tests cover areas including:

* Authentication
* Members
* Events
* Activities
* News
* Notifications
* Contact
* Statistics
* Health checks
* CORS
* AI dependencies
* AI services
* AI retrieval
* AI providers
* AI gateway
* Intent classification

## Frontend

The frontend testing stack includes:

* Unit tests
* Component tests
* Integration tests
* End-to-end tests with Playwright

---

# ðŸ“ Project Structure

```text
KBR/
â”‚
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ ai/
â”‚   â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ schemas/
â”‚   â”‚   â””â”€â”€ services/
â”‚   â”‚
â”‚   â”œâ”€â”€ alembic/
â”‚   â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ tests/
â”‚   â””â”€â”€ requirements.txt
â”‚
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ features/
â”‚   â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ stores/
â”‚   â”‚   â””â”€â”€ test/
â”‚   â”‚
â”‚   â”œâ”€â”€ public/
â”‚   â”œâ”€â”€ package.json
â”‚   â””â”€â”€ vite.config.ts
â”‚
â”œâ”€â”€ .github/
â”‚   â””â”€â”€ workflows/
â”‚
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ .env.example
â”œâ”€â”€ .gitignore
â””â”€â”€ README.md
```

---

# ðŸŒ Frontend Routes

## Public

```text
/
 /about

 /members
 /members/:slug

 /events
 /events/:eventId

 /news
 /news/:slug

 /activities
 /activities/:slug

 /contact
```

## Authentication

```text
/login
/register
/account
/notifications
```

## Administration

```text
/admin

/admin/members
/admin/members/:memberId/edit

/admin/events
/admin/events/new
/admin/events/:eventId/edit

/admin/news
/admin/news/new
/admin/news/:newsId/edit

/admin/activities
/admin/activities/create
/admin/activities/:id/edit

/admin/contact
/admin/statistics
```

Administrative routes are protected through role-based authorization.

---

# âš™ï¸ Local Development

## Prerequisites

Install:

* Python 3.12+
* Node.js
* npm
* PostgreSQL or Docker
* Git

---

## Clone the repository

```bash
git clone https://github.com/Ghaith-Saidani/KBR.git
cd KBR
```

---

## Backend

Create and activate a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r backend/requirements.txt
```

Configure the environment:

```powershell
Copy-Item .env.example .env
```

Run PostgreSQL with Docker Compose:

```powershell
docker compose up -d
```

Run database migrations:

```powershell
alembic -c backend/alembic.ini upgrade head
```

Start the backend:

```powershell
uvicorn backend.app.main:app --reload
```

---

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server will provide the frontend locally.

---

# ðŸ”‘ Environment Configuration

Environment variables are configured through `.env`.

Sensitive credentials must never be committed to Git.

Examples include:

```text
DATABASE_URL
JWT_SECRET
AI_PROVIDER
AI_MODEL
GEMINI_API_KEY
GROQ_API_KEY
```

Use `.env.example` as the template for local configuration.

---

# ðŸ—ºï¸ Roadmap

The current platform provides the foundation for a larger data-driven esports ecosystem.

### Completed / Implemented

* [x] Full-stack React + FastAPI architecture
* [x] PostgreSQL database
* [x] SQLAlchemy ORM
* [x] Alembic migrations
* [x] Authentication
* [x] Role-based authorization
* [x] Member management
* [x] Event management
* [x] Activities management
* [x] News management
* [x] Contact management
* [x] Notifications
* [x] Statistics foundation
* [x] AI assistant
* [x] Database-backed AI context retrieval
* [x] AI provider abstraction
* [x] Backend automated tests
* [x] Frontend automated tests
* [x] End-to-end testing
* [x] GitHub Actions CI
* [x] Docker-based PostgreSQL development environment

### Planned

* [ ] Centralized application activity logging
* [ ] User behavioral analytics pipeline
* [ ] Elasticsearch integration
* [ ] Semantic search
* [ ] Embeddings / vector search
* [ ] Advanced RAG pipeline
* [ ] AI-powered knowledge retrieval
* [ ] Advanced AI agents
* [ ] Power BI dashboards
* [ ] Full application Dockerization
* [ ] Docker-based CI/CD
* [ ] Automated deployment
* [ ] Production monitoring and observability

---

# ðŸŽ¯ Long-Term Architecture

The long-term objective is to evolve KBR from a conventional esports website into a **data-driven and AI-enabled platform**.

```text
                     KBR PLATFORM
                           â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚                         â”‚
          Web Platform              Data Platform
              â”‚                         â”‚
       React + FastAPI             Activity Logs
              â”‚                         â”‚
          PostgreSQL           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚                â”‚                 â”‚
              â”‚           PostgreSQL       Elasticsearch
              â”‚                                  â”‚
              â”‚                           Semantic Search
              â”‚                                  â”‚
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
                             RAG
                              â”‚
                             LLM
                              â”‚
                       AI Assistant
                              â”‚
                              â–¼
                         Power BI
                              â”‚
                              â–¼
                    Business Intelligence
```

The goal is to combine **web development, backend engineering, data engineering, artificial intelligence, analytics, and DevOps** within a single coherent KBR platform.

---

# ðŸ“„ License

This project is developed for **Knights of Bizertin Rise (KBR)**.

---

## ðŸ‘¤ Author

**Ghaith Saidani**

GitHub:
https://github.com/Ghaith-Saidani

---

## ML Risk Analysis

KBR includes a machine-learning risk analysis pipeline and an administrative
page for reviewing the generated risk report.

### Pipeline components

- **Activity feature engineering:** builds HTTP and business activity features,
  including population-aware rolling activity counts, timestamps, HTTP status
  signals, and normalized categorical fields.
- **Behavioral anomaly detection:** uses separate Isolation Forest model
  bundles for HTTP requests and business activities.
- **Explainable risk scoring:** combines behavioral anomaly signals with
  deterministic signals for authentication failures, HTTP errors, activity
  spikes, unusual HTTP methods, suspicious endpoints, and high user activity.
- **Temporal incident detection:** independently identifies authentication
  failure bursts, HTTP error bursts, and short-term HTTP activity bursts.
- **Reporting:** produces a JSON risk report containing risk distributions,
  top risk observations, configuration, and detected temporal incidents.
- **Administration:** the frontend includes the `/admin/ml/risk` page for
  viewing the ML risk report through the backend API.

### Local data and generated artifacts

The pipeline expects the processed activity dataset at:

```text
data/processed/user_activities.csv
```

Model bundles and generated reports are stored locally under:

```text
data/models/
data/reports/anomaly_detection_report.json
data/reports/risk_scoring_report.json
```

Generated models, reports, MLflow databases, and raw/processed datasets are
local artifacts and should not be committed unless a specific sanitized
sample is intentionally required for testing or documentation.

### Dependencies

The backend ML pipeline uses NumPy, pandas, scikit-learn, and joblib in
addition to the FastAPI application dependencies. Install all backend
dependencies from the repository root:

```powershell
python -m pip install -r backend/requirements.txt
```

### Running and validating the pipeline

Run the existing model-training/detection scripts from the repository root
in the order required by their inputs, then generate the risk-scoring report.
The risk-scoring stage requires the corresponding model bundles and anomaly
detection report to exist.

Run backend tests with:

```powershell
python -m pytest backend/tests
```

The risk scores and anomaly rankings are analytical signals, not verified
attack labels. Their accuracy should not be claimed without independently
validated ground-truth labels and evaluation.

<!-- KBR MONITORING STACK -->

## Monitoring and Observability

KBR includes a local monitoring and log aggregation stack managed through
Docker Compose.

### Services

| Service | Purpose | Local URL |
|---|---|---|
| Prometheus | Collects backend metrics | http://localhost:9090 |
| Grafana | Dashboards and visualization | http://localhost:3000 |
| Elasticsearch | Stores application and container logs | http://localhost:9200 |
| Fluent Bit | Collects Docker container logs and forwards them to Elasticsearch | Internal service |
| MLflow | Machine learning experiment tracking | http://localhost:5000 |

The backend exposes `/health` for health checks and `/metrics` for Prometheus
metrics. Prometheus scrapes the backend every 15 seconds.

### Grafana

The existing dashboard is **KBR - Application Monitoring**. It includes:

- Backend memory usage
- HTTP request rate
- 95th-percentile request latency
- HTTP 5xx error rate

Grafana data sources are provisioned from
`monitoring/grafana/provisioning/datasources/datasources.yml`.

The provisioned sources use the internal Docker Compose addresses:

- Prometheus: `http://prometheus:9090`
- Elasticsearch: `http://elasticsearch:9200`

### Log aggregation

Fluent Bit reads Docker JSON log files, enriches records with the container ID
and application metadata, and forwards them to Elasticsearch.

Configuration files:

- `monitoring/fluent-bit/fluent-bit.conf`
- `monitoring/fluent-bit/docker_metadata.lua`

The Elasticsearch index pattern is `kbr-docker-*`, with `@timestamp` as the
time field. Logs can be explored through Grafana using the Elasticsearch
data source.

### Prometheus configuration

Prometheus configuration is maintained in `monitoring/prometheus.yml`.
The current retention period is 15 days.

### Start and manage the stack

Start services:

```powershell
docker compose up -d
```

Check service status:

```powershell
docker compose ps
```

Inspect logs:

```powershell
docker compose logs --tail=100 backend grafana prometheus elasticsearch fluent-bit
```

Validate the Compose configuration:

```powershell
docker compose config --quiet
```

### Data persistence and security

PostgreSQL, Prometheus, Grafana, Elasticsearch, and Fluent Bit state use
named Docker volumes. Do not use `docker compose down -v` for routine
maintenance because it removes named volumes.

The current Elasticsearch configuration disables built-in security for local
development. Do not expose this configuration directly to an untrusted
network or use it as-is for production. Production deployment requires
appropriate authentication, TLS, secret management, and access controls.

Grafana's administrator password is configured through the `GRAFANA_ADMIN_PASSWORD`
environment variable in the local `.env` file. Do not commit `.env` or other
credentials to version control.
