# CodeGuard AI - Complete Project

A powerful AI-driven code security and bug analysis platform built with FastAPI and Next.js.

## 🚀 Features

- **AI-Powered Analysis**: Intelligent code analysis with AI suggestions
- **Security Scanning**: Automated security vulnerability detection
- **Bug Detection**: Identify potential bugs and code issues
- **Real-time Scans**: WebSocket-based real-time scan progress
- **GitHub Integration**: Direct integration with GitHub repositories
- **Risk Scoring**: Comprehensive risk assessment scoring
- **Finding Details**: Detailed findings with AI-suggested fixes
- **Multi-Project Support**: Manage multiple projects and scans

## 📁 Project Structure

```
codeguard-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── core/
│   │   │   ├── config.py          # Configuration settings
│   │   │   ├── database.py        # Database setup
│   │   │   └── security.py        # JWT & password utilities
│   │   ├── models/                # SQLAlchemy models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py        # Authentication endpoints
│   │   │   │   ├── projects.py    # Project management
│   │   │   │   ├── scans.py       # Scan operations
│   │   │   │   └── users.py       # User profile
│   │   │   └── dependencies.py    # Auth dependencies
│   │   ├── services/              # Business logic services
│   │   ├── static_analysis/       # Static analysis tools
│   │   └── worker/                # Celery tasks
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Dashboard
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   ├── scans/             # Scan history
│   │   │   ├── results/[id]/      # Scan results
│   │   │   └── settings/          # User settings
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── navbar.tsx
│   │   │   └── ui/
│   │   │       └── scan-card.tsx
│   │   ├── lib/
│   │   │   ├── api-client.ts      # HTTP client
│   │   │   ├── auth-service.ts
│   │   │   ├── project-service.ts
│   │   │   └── scan-service.ts
│   │   ├── store/
│   │   │   └── index.ts           # Zustand store
│   │   └── types/
│   ├── package.json
│   ├── .env.local
│   └── .env.example
└── README.md
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM for database operations
- PostgreSQL with pgvector - Advanced data storage
- Celery - Async task queue
- Redis - Caching and message broker
- JWT - Authentication
- Pydantic - Data validation

**Frontend:**
- Next.js 16 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Zustand - State management
- Lucide React - Icon library
- Fetch API - HTTP client

## 📋 Setup Instructions

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL (or use Docker)

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Setup database (using Docker Compose)**
   ```bash
   docker-compose up -d
   ```

5. **Run migrations** (if alembic is set up)
   ```bash
   alembic upgrade head
   ```

6. **Start API server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

   On Windows, reload mode can fail with `PermissionError: [WinError 5] Access is denied`.
   Start normally, or set `CODEGUARD_RELOAD=1` before running `backend\start.bat` when you need hot reload.

   API will be available at: `http://localhost:8000`
   API Docs: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API URL
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

   Frontend will be available at: `http://localhost:3000`

### Docker Compose (Full Stack)

Run everything with one command:

```bash
cd backend
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI Backend (port 8000)

Then start the frontend:
```bash
cd frontend
npm run dev
```

## 🔐 Authentication

The application uses JWT (JSON Web Tokens) for authentication:

1. User registers with email and password
2. Password is hashed using bcrypt
3. Login returns JWT access token
4. All protected endpoints require valid JWT token
5. Token stored in localStorage on client side

### Default Credentials

When first running, you need to register:
- Email: your-email@example.com
- Password: secure-password
- Full Name: Your Name

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token
- `POST /api/v1/auth/logout` - Logout

### Users
- `GET /api/v1/users/me` - Get current user profile

### Projects
- `GET /api/v1/projects/` - List all projects
- `POST /api/v1/projects/` - Create new project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Scans
- `POST /api/v1/scans/` - Trigger new scan
- `GET /api/v1/scans/` - List all scans
- `GET /api/v1/scans/{id}` - Get scan results
- `GET /api/v1/scans/{id}/status` - Get scan status
- `DELETE /api/v1/scans/{id}` - Delete scan

### WebSocket
- `WS /ws/scan-progress` - Real-time scan progress updates

## 🔄 Workflow

1. **Register/Login** - Create account and authenticate
2. **Create Project** - Add a new project with repository URL
3. **Trigger Scan** - Start security analysis on project
4. **View Results** - See findings with risk scores
5. **Review Fixes** - Check AI-suggested fixes
6. **Track History** - View all past scans

## 📊 Security Scanning

The platform performs multiple types of scans:

- **Semgrep Scans** - Pattern-based code analysis
- **Git Secrets Detection** - Secret detection using gitleaks
- **Dependency Scanning** - Vulnerability in dependencies
- **SAST Analysis** - Static application security testing
- **Code Quality** - Bug and code smell detection

## 🚀 Deployment

### Production Environment

1. **Backend Deployment**
   - Update `SECRET_KEY` in `.env`
   - Set `DEBUG=False`
   - Configure database URL for production
   - Use production-grade web server (Gunicorn, Uvicorn workers)

2. **Frontend Deployment**
   - Run `npm run build`
   - Deploy to Vercel, Netlify, or your hosting
   - Configure API endpoint for production

3. **Database**
   - Use managed PostgreSQL service
   - Enable SSL connections
   - Regular backups

4. **Security**
   - Enable HTTPS
   - Configure CORS properly
   - Use environment variables for secrets
   - Implement rate limiting
   - Enable logging and monitoring

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Error**
```
# Check if PostgreSQL is running
docker ps | grep postgres

# Rebuild containers
docker-compose restart
```

**Import Errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Frontend Issues

**API Connection Error**
```
# Check if backend is running on http://localhost:8000/health
# Verify NEXT_PUBLIC_API_URL in .env.local
```

**Build Issues**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📝 Environment Variables

### Backend (.env)
```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=codeguard
SECRET_KEY=your-secret-key
AI_PROVIDER=claude
GITHUB_CLIENT_ID=your-client-id
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions, please open an issue on GitHub or contact the development team.

## ✨ New in v1.1

- **GitHub OAuth** — Sign in with GitHub (`/login` → Continue with GitHub)
- **Real-time scan progress** — WebSocket live updates on results page
- **Scheduled scans** — `/schedules` page with automatic re-scans
- **Team collaboration** — `/teams` create teams and invite members
- **Email alerts** — Optional SMTP notifications when scans complete
- **Celery workers** — Set `USE_CELERY=true` + Redis for production scan queue
- **Dependency scanning** — Unpinned deps and missing lockfile detection
- **Git clone** — Repository URLs are cloned before scanning

### GitHub OAuth setup

1. Create an OAuth App at https://github.com/settings/developers
2. Authorization callback URL: `http://localhost:8000/api/v1/auth/github/callback`
3. Add to `backend/.env`:
   ```
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```

### Google OAuth setup

1. Create an OAuth client in Google Cloud Console
2. Authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`
3. Add to `backend/.env`:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

### Celery (optional)

```bash
# With Docker
cd backend && docker-compose up -d redis celery_worker
# Set in .env: USE_CELERY=true
```

## 🗺️ Roadmap

- [x] GitHub OAuth integration
- [x] Scheduled scans
- [x] Email notifications (SMTP)
- [x] Team collaboration
- [ ] Advanced search and filtering
- [ ] Custom rules engine
- [ ] API rate limiting
- [ ] Advanced reporting
- [ ] Mobile app
- [ ] CI/CD pipeline integration

---

**Happy scanning! 🛡️**
