# CodeGuard AI - Quick Setup

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Run the startup script (Windows):
   ```bash
   start.bat
   ```

   Or manually:
   ```bash
   # Create virtual environment
   python -m venv venv
   venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Initialize database
   python init_db.py

   # Start server
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

   On Windows, avoid `--reload` if you see `PermissionError: [WinError 5] Access is denied`.
   To opt into reload through `start.bat`, run `set CODEGUARD_RELOAD=1` first.

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies and start:
   ```bash
   npm install
   npm run dev
   ```

## Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Troubleshooting

1. **CORS Errors**: Make sure both frontend (port 3000) and backend (port 8000) are running
2. **Database Errors**: Run `python init_db.py` in the backend directory
3. **Port Conflicts**: Change ports in the respective configuration files if needed

## Environment Variables

Backend (.env):
- All required variables are set with development defaults
- No additional configuration needed for local development

Frontend (.env.local):
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
