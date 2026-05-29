# CodeGuard AI

AI-powered code security and bug analysis platform built with FastAPI and Next.js.

CodeGuard AI helps teams register projects, run code scans, track risk scores, review findings, and get suggested fixes through a web dashboard backed by a FastAPI API.

## Features

- AI-assisted code analysis and fix suggestions
- Security vulnerability scanning
- Bug and code quality detection
- Real-time scan progress with WebSockets
- GitHub project integration
- Project, team, report, schedule, and scan management
- JWT-based authentication
- Next.js dashboard with TypeScript and Tailwind CSS

## Tech Stack

**Backend**

- FastAPI
- SQLAlchemy
- SQLite for local development
- PostgreSQL and Redis support through Docker Compose
- JWT authentication
- Pydantic validation

**Frontend**

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- Zustand
- Lucide React

## Project Structure

```text
codeguard-ai/
  backend/      FastAPI API, models, schemas, scanners, services, workers
  frontend/     Next.js application, pages, components, API clients, store
  README.md     Detailed project documentation
```

## Quick Start

### Backend

```bash
cd codeguard-ai/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend API: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd codeguard-ai/frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`

## Environment

Backend settings are based on:

```bash
codeguard-ai/backend/.env.example
```

Frontend settings are based on:

```bash
codeguard-ai/frontend/.env.example
```

Do not commit real `.env` files. They are ignored by Git.

## Useful Commands

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend lint
cd codeguard-ai/frontend
npm run lint
```

## Documentation

More detailed setup and project notes are available inside `codeguard-ai/`:

- `README.md`
- `QUICKSTART.md`
- `SETUP.md`
- `OAUTH_SETUP.md`
