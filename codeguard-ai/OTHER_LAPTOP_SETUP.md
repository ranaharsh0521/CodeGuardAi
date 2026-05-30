# CodeGuard AI - Other Laptop Setup

## One-Click Windows Setup

1. Install prerequisites:
   - Node.js 18+
   - Python 3.11+ with "Add python.exe to PATH" enabled

2. Copy or clone this project to the new laptop.

3. Open the `codeguard-ai` folder and double-click:
   `setup-one-click.bat`

The script will:
- create `backend/.env` from `backend/.env.example` if missing
- create the backend virtual environment
- install Python dependencies
- initialize the SQLite database
- create `frontend/.env.local` if missing
- install frontend dependencies
- start backend and frontend

URLs:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

OAuth note:
If Google/GitHub login does not work, check values in `backend/.env` and restart the backend.
