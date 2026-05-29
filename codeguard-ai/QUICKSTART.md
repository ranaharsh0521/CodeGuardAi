# 🚀 CodeGuard AI - Quick Start Guide

Get the complete CodeGuard AI project up and running in minutes!

## ⚡ 5-Minute Setup

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone/Navigate to project
cd backend

# 2. Start all services
docker-compose up -d

# 3. Check services are running
docker-compose ps

# 4. In another terminal, start frontend
cd ../frontend
npm install
npm run dev
```

Access:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app
```

On Windows, run without `--reload` if startup fails with `PermissionError: [WinError 5] Access is denied`.
For `start.bat`, set `CODEGUARD_RELOAD=1` first only when you specifically need hot reload.

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📝 First Run

1. **Create Account**
   - Go to http://localhost:3000
   - Click "Sign Up"
   - Enter email, password, full name
   - Click "Create Account"

2. **Create Project**
   - Dashboard opens automatically
   - Click "+ New Project"
   - Enter project name
   - Enter GitHub URL (optional)
   - Click "Create"

3. **Trigger Scan**
   - Click "Scan Now" on your project
   - Scan starts and shows real-time progress
   - Results appear in scan details page

4. **Review Results**
   - See Risk Score
   - Check findings by severity
   - Read AI suggestions for fixes

## 🔧 Configuration

### Backend (.env)
```
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=codeguard

SECRET_KEY=dev-secret-key-change-in-production

AI_API_KEY=your_api_key_here
GITHUB_CLIENT_ID=your_id
GITHUB_CLIENT_SECRET=your_secret
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📁 Project Structure

```
codeguard-ai/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Data schemas
│   │   └── services/ # Business logic
│   └── docker-compose.yml
├── frontend/         # Next.js frontend
│   ├── src/
│   │   ├── app/      # Pages
│   │   ├── components/ # React components
│   │   └── lib/      # Services & utilities
│   └── package.json
└── README.md
```

## 🎯 Key Features Implemented

✅ **Authentication System**
- User registration with email/password
- JWT token-based auth
- Secure password hashing

✅ **Project Management**
- Create and manage projects
- Store repository URLs
- Project listing and details

✅ **Security Scanning**
- Trigger scans on projects
- Real-time scan progress
- Scan history tracking
- Detailed vulnerability findings

✅ **Results & Analysis**
- Comprehensive finding details
- AI-suggested fixes
- Risk scoring system
- Severity-based filtering

✅ **User Interface**
- Modern dark theme
- Responsive design
- Dashboard with statistics
- Intuitive navigation

## 🔌 API Usage Examples

### Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure-password",
    "full_name": "John Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure-password"
  }'
```

### Create Project
```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "Project description",
    "repository_url": "https://github.com/user/repo"
  }'
```

### Trigger Scan
```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "commit_hash": "abc123def456"
  }'
```

## 🆘 Troubleshooting

**Port already in use?**
```bash
# Kill process on port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

**Database connection error?**
```bash
# Check Docker containers
docker-compose logs db

# Restart containers
docker-compose restart
```

**Frontend won't connect to API?**
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify backend is running: `curl http://localhost:8000/health`
- Check browser console for CORS errors

**Dependencies missing?**
```bash
# Backend
pip install --force-reinstall -r requirements.txt

# Frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentation

- [Full README](./README.md) - Complete documentation
- [Backend API Docs](http://localhost:8000/docs) - Swagger UI
- [Frontend Code](./frontend/src) - Component structure

## 🎨 UI/UX Features

- **Responsive Design** - Works on desktop, tablet, mobile
- **Dark Theme** - Easy on the eyes
- **Real-time Updates** - WebSocket integration
- **Loading States** - Smooth user experience
- **Error Handling** - Clear error messages
- **Accessibility** - Semantic HTML, ARIA labels

## 🔒 Security Features

- JWT authentication with secure tokens
- Password hashing using bcrypt
- CORS protection
- Environment variables for secrets
- Database encryption ready
- SQL injection prevention (SQLAlchemy ORM)

## 🚀 Next Steps

1. **Customize Configuration**
   - Update API keys in `.env`
   - Configure GitHub integration
   - Set up email notifications

2. **Extend Features**
   - Add scheduled scans
   - Implement custom rules
   - Build team collaboration
   - Create admin dashboard

3. **Deploy**
   - Deploy backend to production server
   - Deploy frontend to hosting service
   - Setup CI/CD pipelines
   - Configure monitoring

## 💡 Tips

- Use `npm run dev` for frontend development with hot reload
- Use `--reload` flag with uvicorn for backend hot reload
- Check `docker-compose logs` for service logs
- Use API docs at `/docs` to test endpoints
- Enable browser DevTools for debugging

## 📞 Need Help?

- Check logs: `docker-compose logs service-name`
- Review error messages in console
- Check `.env` configuration
- Restart all services: `docker-compose down && docker-compose up`

---

**You're all set! Start scanning your code now! 🛡️**
