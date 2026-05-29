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
    "Main CodeGuard AI project assistant hoon. Main sirf is platform ke security scans, "
    "findings, fixes, auth, reports, teams, schedules, uploads, backend/frontend errors, "
    "aur code-security workflow par help kar sakta hoon. CodeGuard se related error, "
    "scan finding, file path, ya question bhejo."
)

ASSISTANT_RULES = (
    "1. Scope: sirf CodeGuard AI, code security, scans, findings, auth, reports, uploads, teams, schedules, aur debugging.",
    "2. Safety: secrets, tokens, passwords, ya .env values reveal/copy mat karna; rotate karne ko bolo.",
    "3. Output: short, actionable steps; zarurat ho to exact page/API/file mention karo.",
    "4. Vulnerabilities: risk explain karo, fix steps do, aur re-scan/triage action suggest karo.",
    "5. Missing context: guess karne ke bajay specific scan id, file, endpoint, ya error log maango.",
    "6. Language: user Hindi/Hinglish me pooche to Hinglish me jawab do.",
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
            "CodeGuard AI Assistant ready hai.\n\n"
            "Aap pooch sakte ho:\n"
            "- scan kaise start/verify karein\n"
            "- finding ka risk aur fix\n"
            "- OAuth/login/backend error\n"
            "- project detail, comparison, reports, teams, schedules\n\n"
            "Specific scan id, error log, ya code snippet bhejo."
        )

    if not _is_project_related(message):
        return PROJECT_SCOPE_REPLY

    if any(word in text for word in GREETING_WORDS):
        return (
            "Namaste! Main CodeGuard AI Assistant hoon.\n\n"
            "Main project ke andar ye help karta hoon:\n"
            "- scans aur findings explain/fix\n"
            "- auth/OAuth/JWT errors debug\n"
            "- upload, reports, teams, schedules workflow\n"
            "- FastAPI/Next.js project errors\n\n"
            "Apna error, scan id, finding, ya code paste karo."
        )

    if any(word in text for word in ["rule", "rules", "scope", "allowed", "chat"]):
        return (
            "CodeGuard AI chat rules:\n"
            + "\n".join(f"- {rule}" for rule in ASSISTANT_RULES)
        )

    if any(word in text for word in ["scan", "finding", "vulnerability", "security", "risk", "semgrep", "gitleaks"]):
        return (
            "CodeGuard scan workflow:\n"
            "1. Dashboard se project create/import karo ya /upload se files bhejo\n"
            "2. Scan Now click karo; progress /results/{scan_id} par live dikhega\n"
            "3. Critical/error findings pehle fix karo\n"
            "4. Finding status use karo: open, resolved, ignored, false_positive\n"
            "5. Fix ke baad dobara scan run karo aur comparison/risk trend check karo\n\n"
            "Agar aap finding paste karoge, main exact risk aur fix steps dunga."
        )

    if any(word in text for word in ["password", "jwt", "token", "auth", "login", "oauth", "github", "google"]):
        return (
            "CodeGuard auth/OAuth checklist:\n"
            "- Backend auth file: backend/app/api/endpoints/auth.py\n"
            "- Google callback URI: http://localhost:8000/api/v1/auth/google/callback\n"
            "- GitHub callback URI: http://localhost:8000/api/v1/auth/github/callback\n"
            "- Frontend callback page: /auth/oauth/callback\n"
            "- JWT token localStorage me store hota hai; protected APIs get_current_user use karte hain\n"
            "- .env secrets frontend me expose mat karo; leaked credentials rotate karo\n\n"
            "Agar 500/redirect issue hai, backend_run.log ka latest traceback bhejo."
        )

    if any(word in text for word in ["upload", "file", "scan upload", "zip", "code upload"]):
        return (
            "CodeGuard upload flow:\n"
            "- Frontend page: /upload\n"
            "- Backend API: POST /api/v1/upload/upload-scan\n"
            "- Supported extensions API: GET /api/v1/upload/supported-extensions\n"
            "- Upload ke baad scan result /results/{scan_id} par open hota hai\n"
            "- ZIP/local files scan karte waqt node_modules, .next, venv jaise folders skip hote hain\n\n"
            "Upload fail ho raha hai to file type, size, aur backend_run.log ka error bhejo."
        )

    if any(word in text for word in ["report", "pdf", "export", "download"]):
        return (
            "CodeGuard reports:\n"
            "- PDF: GET /api/v1/reports/{scan_id}/pdf\n"
            "- JSON: GET /api/v1/reports/{scan_id}/json\n"
            "- UI: /results/{scan_id} par PDF/JSON buttons\n"
            "- Report tabhi useful hai jab scan completed ho\n\n"
            "Report error aaye to scan id aur response status bhejo."
        )

    if any(word in text for word in ["fix", "bug", "error", "crash", "500", "404", "cors"]):
        return (
            "CodeGuard debug steps:\n"
            "1. Backend error: backend/backend_run.log ka latest traceback check karo\n"
            "2. Frontend error: frontend/frontend_run.log aur browser console check karo\n"
            "3. API docs: http://localhost:8000/docs par endpoint test karo\n"
            "4. 401: token/login issue; 403: permission issue; 404: id/route issue; 500: backend traceback\n"
            "5. Fix ke baad npm run lint, npm run build, aur backend verify script run karo\n\n"
            "Exact error paste karo, main file-level fix bataunga."
        )

    if any(word in text for word in ["team", "member", "invite", "project"]):
        return (
            "CodeGuard teams/projects:\n"
            "- Projects dashboard par create/import hote hain\n"
            "- Project detail page: /projects/{project_id}\n"
            "- Team page: /teams; owner/admin invite kar sakte hain\n"
            "- Shared team projects members ko visible hote hain\n"
            "- Scan history project detail aur /scans dono jagah dikhti hai\n\n"
            "Project access issue ho to user role, team id, aur project id bhejo."
        )

    if any(word in text for word in ["compare", "comparison", "trend", "resolved", "ignored", "false positive", "false_positive"]):
        return (
            "CodeGuard comparison/triage:\n"
            "- Results page par finding status set karo: open/resolved/ignored/false_positive\n"
            "- Project detail page latest scan ko previous completed scan se compare karta hai\n"
            "- Comparison metrics: new findings, resolved findings, unchanged findings, risk delta\n"
            "- Risk trend last completed scans ka visual summary dikhata hai\n\n"
            "Agar comparison galat lag raha hai to current scan id aur base scan id bhejo."
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
        "Main CodeGuard AI Assistant hoon. Main project-specific help deta hoon:\n"
        "- scans, findings, risk score, comparison\n"
        "- auth/OAuth/JWT/login\n"
        "- upload, reports, teams, schedules\n"
        "- FastAPI backend aur Next.js frontend errors\n\n"
        "Please exact error, endpoint, scan id, ya code snippet bhejo."
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
