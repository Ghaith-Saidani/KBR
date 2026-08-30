# Knights of Bizertin Rise (KBR)

Official web platform for **Knights of Bizertin Rise (KBR)**, an esports organization based in Bizerte, Tunisia.

The project provides a modern full-stack platform for managing and presenting KBR's members, events, activities, news, communications, notifications, statistics, and AI-powered assistance.

---

## 📌 Project Overview

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

# 🏗️ Architecture

```text
                         KBR PLATFORM
                              │
             ┌────────────────┴────────────────┐
             │                                 │
        React Frontend                    FastAPI Backend
             │                                 │
     ┌───────┼────────┐              ┌─────────┼─────────┐
     │       │        │              │         │         │
   Pages  Features    AI           APIs     Services     AI
     │       │        │              │         │         │
     └───────┴────────┘              └─────────┼─────────┘
                                               │
                                          SQLAlchemy
                                               │
                                          PostgreSQL
                                               │
                              ┌────────────────┴───────────────┐
                              │                                │
                         Application                    AI / Retrieval
                            Data                            Layer
```

The project follows a modular architecture separating presentation, API, business logic, persistence, and AI responsibilities.

---

# 🛠️ Technology Stack

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
    │
    ▼
AI Router
    │
    ▼
AI Service
    │
    ├── Intent Classification
    │
    ├── Context Retrieval
    │
    ├── Context Formatting
    │
    ▼
Model Gateway
    │
    ├── Gemini
    └── Groq
    │
    ▼
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

# 🔐 Authentication & Authorization

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

# 👥 Members

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

# 📅 Events

The platform provides both public event presentation and administrative event management.

Administrators/staff can:

* View events
* Create events
* Edit events
* Manage event information

Public users can access event listings and individual event detail pages.

---

# 📰 News

KBR includes a complete news/content management section.

Features include:

* Public news listing
* News detail pages
* Administrative news management
* News creation
* News editing
* Slug-based news URLs

---

# 🚀 Activities

Activities and projects are managed through a dedicated module.

Features include:

* Public activity listing
* Activity detail pages
* Administrative activity management
* Activity creation
* Activity editing

---

# 🔔 Notifications

Authenticated users have access to a notification system through their personal account area.

---

# 📩 Contact

The platform includes:

* Public contact form
* Backend contact processing
* Administrative contact management

---

# 📊 Statistics

KBR includes a statistics subsystem for monitoring application activity and presenting administrative metrics.

The statistics architecture provides a foundation for future behavioral analytics and business intelligence.

The planned evolution includes:

```text
User Activity
     │
     ▼
Event / Activity Logging
     │
     ▼
Data Processing
     │
     ├── PostgreSQL
     └── Elasticsearch
             │
             ▼
          Analytics
             │
             ▼
          Power BI
```

---

# 🤖 AI Assistant

KBR includes an integrated AI assistant accessible from the frontend.

The assistant is designed specifically around KBR's own information rather than functioning as a generic chatbot.

Current architecture includes:

```text
Frontend AI Chat
       │
       ▼
POST /ai/chat
       │
       ▼
Intent Processing
       │
       ▼
KBR Context Retrieval
       │
       ▼
Context Formatting
       │
       ▼
Model Gateway
       │
       ▼
AI Provider
       │
       ▼
Response
```

The backend controls model/provider configuration, preventing the frontend from arbitrarily selecting AI providers or models.

---

# 🗄️ Database

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

# 🐳 Docker

Docker Compose is currently used to provision the PostgreSQL development database.

Current infrastructure includes:

```text
Docker Compose
      │
      ▼
PostgreSQL 17
      │
      ▼
Persistent volume
```

The long-term architecture will extend Dockerization to the complete application:

```text
Docker Compose
├── Frontend
├── Backend
├── PostgreSQL
├── Elasticsearch
└── Supporting services
```

---

# 🔄 Continuous Integration

The project includes GitHub Actions CI.

The CI pipeline performs automated checks including:

```text
Push
 │
 ▼
GitHub Actions
 │
 ├── PostgreSQL service
 ├── Python environment
 ├── Backend compilation
 ├── Alembic migrations
 └── Pytest
```

The frontend also provides automated linting, testing, and production build checks.

---

# 🧪 Testing

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

# 📁 Project Structure

```text
KBR/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── alembic/
│   ├── scripts/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── stores/
│   │   └── test/
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── .github/
│   └── workflows/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# 🌐 Frontend Routes

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

# ⚙️ Local Development

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

# 🔑 Environment Configuration

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

# 🗺️ Roadmap

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

# 🎯 Long-Term Architecture

The long-term objective is to evolve KBR from a conventional esports website into a **data-driven and AI-enabled platform**.

```text
                     KBR PLATFORM
                           │
              ┌────────────┴────────────┐
              │                         │
          Web Platform              Data Platform
              │                         │
       React + FastAPI             Activity Logs
              │                         │
          PostgreSQL           ┌────────┴────────┐
              │                │                 │
              │           PostgreSQL       Elasticsearch
              │                                  │
              │                           Semantic Search
              │                                  │
              └───────────────┬──────────────────┘
                              │
                             RAG
                              │
                             LLM
                              │
                       AI Assistant
                              │
                              ▼
                         Power BI
                              │
                              ▼
                    Business Intelligence
```

The goal is to combine **web development, backend engineering, data engineering, artificial intelligence, analytics, and DevOps** within a single coherent KBR platform.

---

# 📄 License

This project is developed for **Knights of Bizertin Rise (KBR)**.

---

## 👤 Author

**Ghaith Saidani**

GitHub:
https://github.com/Ghaith-Saidani
