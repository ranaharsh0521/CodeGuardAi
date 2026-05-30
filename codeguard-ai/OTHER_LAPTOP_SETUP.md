# CodeGuard AI - One Click Setup

For another Windows laptop:

1. Install Node.js 18+.
2. Install Python 3.11+ and enable "Add python.exe to PATH".
3. Copy or clone this project.
4. Open the `codeguard-ai` folder.
5. Double-click `setup-one-click.bat`.

The batch file will create env files, create the backend virtual environment, install dependencies, initialize the database, start backend/frontend, wait for the frontend, and open the app.

URLs:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Logs:
- `logs/backend.log`
- `logs/frontend.log`

OAuth note:
Google/GitHub login uses values from `backend/.env`. If login does not work, check `backend/.env`, then double-click `setup-one-click.bat` again.
