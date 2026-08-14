# Gatekeeper.ai

**Gatekeeper.ai** is an LLM Prompt-Injection Firewall — a proxy service that sits between client applications and LLM APIs (OpenAI, Anthropic, etc.) to detect and block prompt injection, jailbreak attempts, and data exfiltration in real time.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI |
| Frontend | React, Vite, Tailwind CSS |
| Database | PostgreSQL |
| Vector Search | ChromaDB (Phase 2+) |
| Containers | Docker Compose |

## Folder Structure

```
gatekeeper.ai/
├── backend/          # FastAPI application (feature-based modules)
├── frontend/         # React dashboard (feature-based modules)
├── docker/           # Dockerfiles and docker-compose
├── docs/             # Architecture notes and API documentation
└── scripts/          # Dev and setup scripts
```

See each subdirectory's `README.md` for details on its role.

## Quick Start (Phase 2)

> Setup instructions will be completed in Phase 2. For now, use the stubs below to verify the stack boots.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: [http://localhost:8000/health](http://localhost:8000/health)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: [http://localhost:5173](http://localhost:5173)

### Docker Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

## License

TBD
