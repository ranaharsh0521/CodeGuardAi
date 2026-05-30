from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any
from app.services.ai_suggester import AISuggester
from app.api.dependencies import get_current_user_optional
from app.models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str


PROJECT_SCOPE_REPLY = (
    "I am the CodeGuard AI project assistant. I can help only with this platform's "
    "security scans, findings, fixes, auth, reports, teams, schedules, uploads, "
    "backend/frontend errors, and code-security workflow. Send a CodeGuard-related "
    "error, scan finding, file path, or question."
)

ASSISTANT_RULES = (
    "1. Scope: only CodeGuard AI, code security, scans, findings, auth, reports, uploads, teams, schedules, and debugging.",
    "2. Safety: never reveal or copy secrets, tokens, passwords, or .env values; tell the user to rotate exposed credentials.",
    "3. Output: keep answers short and actionable; mention the exact page/API/file when useful.",
    "4. Vulnerabilities: explain the risk, give fix steps, and suggest re-scan/triage actions.",
    "5. Missing context: ask for a specific scan id, file, endpoint, or error log instead of guessing.",
    "6. Language: respond in English.",
)

PROJECT_KEYWORDS = {
    "api",
    "auth",
    "authentication",
    "backend",
    "bug",
    "code",
    "codeguard",
    "cors",
    "debug",
    "dependency",
    "endpoint",
    "error",
    "fastapi",
    "finding",
    "fix",
    "frontend",
    "github",
    "gitleaks",
    "google",
    "jwt",
    "login",
    "oauth",
    "password",
    "pdf",
    "project",
    "report",
    "scan",
    "scanner",
    "secret",
    "security",
    "semgrep",
    "team",
    "token",
    "upload",
    "vulnerability",
    "websocket",
    "zip",
    "rule",
    "rules",
    "assistant",
    "chat",
    "compare",
    "comparison",
    "risk",
    "trend",
    "schedule",
    "scheduler",
    "env",
    "database",
    "sqlite",
    "next",
    "nextjs",
    "react",
    "typescript",
    "tailwind",
    "uvicorn",
    "report",
    "pdf",
    "json",
}

GREETING_WORDS = {"hi", "hey", "hello", "hii", "hy", "namaste"}


def _is_project_related(message: str) -> bool:
    text = message.strip().lower()
    if not text:
        return True

    words = {word.strip(".,!?;:()[]{}\"'`") for word in text.split()}
    if words & GREETING_WORDS:
        return True

    return any(keyword in text for keyword in PROJECT_KEYWORDS)


def _local_assistant_reply(message: str) -> str:
    """Deterministic fallback when AI provider is unavailable."""
    text = message.strip().lower()
    if not text:
        return (
            "CodeGuard AI Assistant is ready.\n\n"
            "You can ask about:\n"
            "- how to start or verify a scan\n"
            "- finding risk and fixes\n"
            "- OAuth/login/backend error\n"
            "- project detail, comparison, reports, teams, schedules\n\n"
            "Send a specific scan id, error log, or code snippet."
        )

    if not _is_project_related(message):
        return PROJECT_SCOPE_REPLY

    if any(word in text for word in GREETING_WORDS):
        return (
            "Hello! I am the CodeGuard AI Assistant.\n\n"
            "I can help with these project areas:\n"
            "- explain and fix scans and findings\n"
            "- debug auth/OAuth/JWT errors\n"
            "- upload, reports, teams, schedules workflow\n"
            "- FastAPI/Next.js project errors\n\n"
            "Paste your error, scan id, finding, or code."
        )

    if any(word in text for word in ["rule", "rules", "scope", "allowed", "chat"]):
        return (
            "CodeGuard AI chat rules:\n"
            + "\n".join(f"- {rule}" for rule in ASSISTANT_RULES)
        )

    if any(word in text for word in ["scan", "finding", "vulnerability", "security", "risk", "semgrep", "gitleaks"]):
        return (
            "CodeGuard scan workflow:\n"
            "1. Create or import a project from the dashboard, or upload files from /upload\n"
            "2. Click Scan Now; progress appears live on /results/{scan_id}\n"
            "3. Fix critical/error findings first\n"
            "4. Use finding statuses: open, resolved, ignored, false_positive\n"
            "5. Run another scan after fixing issues and check the comparison/risk trend\n\n"
            "If you paste a finding, I can explain the exact risk and fix steps."
        )

    if any(word in text for word in ["password", "jwt", "token", "auth", "login", "oauth", "github", "google"]):
        return (
            "CodeGuard auth/OAuth checklist:\n"
            "- Backend auth file: backend/app/api/endpoints/auth.py\n"
            "- Google callback URI: http://localhost:8000/api/v1/auth/google/callback\n"
            "- GitHub callback URI: http://localhost:8000/api/v1/auth/github/callback\n"
            "- Frontend callback page: /auth/oauth/callback\n"
            "- The JWT token is stored in localStorage; protected APIs use get_current_user\n"
            "- Do not expose .env secrets in the frontend; rotate leaked credentials\n\n"
            "For a 500 or redirect issue, send the latest traceback from backend_run.log."
        )

    if any(word in text for word in ["upload", "file", "scan upload", "zip", "code upload"]):
        return (
            "CodeGuard upload flow:\n"
            "- Frontend page: /upload\n"
            "- Backend API: POST /api/v1/upload/upload-scan\n"
            "- Supported extensions API: GET /api/v1/upload/supported-extensions\n"
            "- After upload, the scan result opens on /results/{scan_id}\n"
            "- ZIP/local scans skip folders such as node_modules, .next, and venv\n\n"
            "If upload fails, send the file type, size, and backend_run.log error."
        )

    if any(word in text for word in ["report", "pdf", "export", "download"]):
        return (
            "CodeGuard reports:\n"
            "- PDF: GET /api/v1/reports/{scan_id}/pdf\n"
            "- JSON: GET /api/v1/reports/{scan_id}/json\n"
            "- UI: PDF/JSON buttons on /results/{scan_id}\n"
            "- Reports are useful after a scan has completed\n\n"
            "For report errors, send the scan id and response status."
        )

    if any(word in text for word in ["fix", "bug", "error", "crash", "500", "404", "cors"]):
        return (
            "CodeGuard debug steps:\n"
            "1. Backend error: check the latest traceback in backend/backend_run.log\n"
            "2. Frontend error: check frontend/frontend_run.log and the browser console\n"
            "3. API docs: test the endpoint at http://localhost:8000/docs\n"
            "4. 401: token/login issue; 403: permission issue; 404: id/route issue; 500: backend traceback\n"
            "5. After fixing, run npm run lint, npm run build, and the backend verify script\n\n"
            "Paste the exact error and I can point to the file-level fix."
        )

    if any(word in text for word in ["team", "member", "invite", "project"]):
        return (
            "CodeGuard teams/projects:\n"
            "- Projects are created/imported from the dashboard\n"
            "- Project detail page: /projects/{project_id}\n"
            "- Team page: /teams; owners/admins can invite members\n"
            "- Shared team projects are visible to members\n"
            "- Scan history appears on both the project detail page and /scans\n\n"
            "For project access issues, send the user role, team id, and project id."
        )

    if any(word in text for word in ["compare", "comparison", "trend", "resolved", "ignored", "false positive", "false_positive"]):
        return (
            "CodeGuard comparison/triage:\n"
            "- Set finding status on the results page: open/resolved/ignored/false_positive\n"
            "- The project detail page compares the latest scan with the previous completed scan\n"
            "- Comparison metrics: new findings, resolved findings, unchanged findings, risk delta\n"
            "- Risk trend shows a visual summary of recent completed scans\n\n"
            "If the comparison looks wrong, send the current scan id and base scan id."
        )

    if any(word in text for word in ["run", "start", "uvicorn", "next", "localhost", "port"]):
        return (
            "CodeGuard run commands:\n"
            "Backend:\n"
            "cd backend\n"
            "venv\\Scripts\\activate\n"
            "uvicorn app.main:app --host 0.0.0.0 --port 8000\n\n"
            "Frontend:\n"
            "cd frontend\n"
            "npm run dev\n\n"
            "URLs: frontend http://localhost:3000, backend http://localhost:8000, docs http://localhost:8000/docs"
        )

    return (
        "I am the CodeGuard AI Assistant. I provide project-specific help for:\n"
        "- scans, findings, risk score, comparison\n"
        "- auth/OAuth/JWT/login\n"
        "- upload, reports, teams, schedules\n"
        "- FastAPI backend and Next.js frontend errors\n\n"
        "Please send the exact error, endpoint, scan id, or code snippet."
    )


@router.post("/", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Chat endpoint for the CodeGuard AI project assistant.
    """
    if not _is_project_related(request.message):
        return ChatResponse(reply=PROJECT_SCOPE_REPLY)

    ai_suggester = AISuggester()

    if not ai_suggester.api_key:
        return ChatResponse(reply=_local_assistant_reply(request.message))

    rules_text = "\n".join(f"- {rule}" for rule in ASSISTANT_RULES)
    user_name = current_user.full_name if current_user else "Guest user"

    prompt = f"""You are CodeGuard AI, an intelligent security assistant built into the CodeGuard AI platform.

## Platform Context
CodeGuard AI is a code security and bug analysis platform with these features:
- Code scanning (Semgrep, Gitleaks, custom analyzers)
- AI-powered fix suggestions for vulnerabilities
- PDF report generation
- Real-time scan progress via WebSocket
- GitHub/Google OAuth authentication
- Team collaboration and project management
- Scheduled scans
- File/ZIP upload for scanning
- Project detail page with risk trend and scan comparison
- Finding workflow statuses: open, resolved, ignored, false_positive

## Tech Stack
- Backend: FastAPI (Python), SQLite/PostgreSQL, JWT auth
- Frontend: Next.js 16, TypeScript, Tailwind CSS, Zustand
- AI: OpenAI GPT-4o / Claude / Grok

## Important Routes/APIs
- Frontend: /, /projects/[id], /scans, /results/[id], /upload, /teams, /schedules, /settings, /chat
- Backend APIs: /api/v1/auth, /api/v1/projects, /api/v1/scans, /api/v1/upload, /api/v1/reports, /api/v1/teams, /api/v1/schedules, /api/v1/chat
- WebSocket: /ws/scan-progress

## Mandatory Response Rules
{rules_text}

## Current User
Name: {user_name}
Context: {request.context}

## User Message
{request.message}
"""

    try:
        reply = await ai_suggester.get_chat_response(prompt)
        if not reply:
            return ChatResponse(
                reply="I'm having trouble generating a response right now. Please try again."
            )
        return ChatResponse(reply=reply)
    except Exception:
        return ChatResponse(reply=_local_assistant_reply(request.message))
