# CodeGuard AI - One Click Setup

For another Windows laptop:

1. Copy or clone this project.
2. Open the `codeguard-ai` folder.
3. Double-click `setup-one-click.bat`.

The batch file will check Node.js and Python. If either one is missing and Windows `winget` is available, it will install them automatically. Then it will create env files, create the backend virtual environment, install dependencies, initialize the database, start backend/frontend, wait for the frontend, and open the app.

If automatic Node.js/Python installation fails, install these manually and run the batch file again:
- Node.js 18+
- Python 3.11+ with "Add python.exe to PATH" enabled

URLs:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Logs:
- `logs/backend.log`
- `logs/frontend.log`

OAuth note:
Google/GitHub login uses values from `backend/.env`. If login does not work, check `backend/.env`, then double-click `setup-one-click.bat` again.
