# CodeGuard AI - Complete Setup & Troubleshooting Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- PostgreSQL (optional - SQLite used by default)
- Git

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Or use the automated script:**
```bash
cd backend
start.bat  # Windows
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
PROJECT_NAME="CodeGuard AI"
API_V1_STR="/api/v1"
POSTGRES_SERVER="localhost"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_DB="codeguard"
POSTGRES_PORT="5432"
SECRET_KEY="development_secret_key_change_in_production"
AI_PROVIDER="claude"  # or "grok"
AI_API_KEY=""  # Optional - for AI features
GITHUB_CLIENT_ID=""  # Optional - for GitHub integration
GITHUB_CLIENT_SECRET=""  # Optional
REDIS_URL="redis://localhost:6379/0"  # Optional - for background tasks
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 🎯 Features

### ✅ Implemented Features

1. **Authentication System**
   - User registration/login
   - JWT token-based auth
   - Protected routes

2. **Project Management**
   - Create/edit/delete projects
   - Repository URL support
   - Project dashboard

3. **Security Scanning**
   - Static analysis (Semgrep fallback)
   - Secret detection (Gitleaks fallback)
   - Risk scoring
   - Background processing

4. **AI Integration**
   - AI-powered fix suggestions
   - Interactive chat assistant
   - Code analysis explanations

5. **User Interface**
   - Modern dark theme
   - Responsive design
   - Real-time updates
   - Error handling

6. **Reporting**
   - Detailed scan results
   - Findings categorization
   - Export capabilities

### 🔄 Demo Mode

When security tools (Semgrep/Gitleaks) are not installed, the application runs in **demo mode** with sample findings to showcase functionality.

## 🐛 Troubleshooting

### Common Issues

#### 1. CORS Errors
**Problem:** `Access-Control-Allow-Origin` errors
**Solution:** 
- Ensure backend is running on port 8000
- Frontend should be on port 3000
- Check CORS configuration in `main.py`

#### 2. Database Connection Issues
**Problem:** Database connection failures
**Solution:**
```bash
cd backend
python init_db.py  # Recreate tables
```

#### 3. Authentication Issues
**Problem:** Login/signup not working
**Solution:**
- Check if backend is running
- Verify API endpoints in browser: `http://localhost:8000/docs`
- Clear browser localStorage

#### 4. Scan Failures
**Problem:** Scans fail or show no results
**Solution:**
- Check backend logs
- Verify project repository URL
- Demo findings will show if tools aren't installed

#### 5. AI Features Not Working
**Problem:** Chat assistant returns errors
**Solution:**
- Set `AI_API_KEY` in backend `.env`
- Choose correct `AI_PROVIDER` (claude/grok)
- Check API key validity

### Development Tips

1. **API Documentation:** Visit `http://localhost:8000/docs` for interactive API docs
2. **Database Reset:** Delete `codeguard.db` and run `python init_db.py`
3. **Frontend Debugging:** Check browser console for errors
4. **Backend Logs:** Monitor terminal output for error messages

## 🔒 Security Tools Setup (Optional)

### Install Semgrep
```bash
pip install semgrep
```

### Install Gitleaks
```bash
# Download from: https://github.com/gitleaks/gitleaks/releases
# Add to PATH
```

## 🚀 Production Deployment

### Backend (FastAPI)
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend (Next.js)
```bash
npm run build
npm start
```

### Docker (Optional)
```bash
docker-compose up -d
```

## 📊 Usage Examples

### 1. Create a Project
1. Navigate to dashboard
2. Click "New Project"
3. Enter project details
4. Click "Create"

### 2. Run a Scan
1. Select project from dashboard
2. Click "Scan Now"
3. Monitor progress in real-time
4. View results when complete

### 3. Use AI Assistant
1. Navigate to "AI Assistant"
2. Ask questions about security
3. Get code suggestions
4. Review explanations

## 🤝 Support

- **Issues:** Check console logs and error messages
- **Features:** All core functionality is implemented
- **Demo Mode:** Works without external tools
- **Documentation:** This guide covers all scenarios

## 📈 Performance Notes

- **Scan Speed:** Depends on project size and tools
- **AI Response:** Requires valid API key
- **Real-time Updates:** Polls every 3 seconds
- **Database:** SQLite for development, PostgreSQL for production

---

**Status:** ✅ Fully functional with comprehensive error handling and fallbacks