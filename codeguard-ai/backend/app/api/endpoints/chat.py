from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from app.services.ai_suggester import AISuggester
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    reply: str


PROJECT_SCOPE_REPLY = (
    "Main CodeGuard AI project assistant hoon. Main sirf CodeGuard AI platform, "
    "security scans, vulnerabilities, code review, debugging, auth, reports, teams, "
    "projects, uploads, aur is project ke backend/frontend workflow par help kar sakta hoon. "
    "Please apna CodeGuard-related question, code, error, ya scan finding share karo."
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
        return "CodeGuard AI yahan hai. Scan findings, vulnerabilities, ya code security ke baare mein poochho."

    if not _is_project_related(message):
        return PROJECT_SCOPE_REPLY

    if any(word in text for word in GREETING_WORDS):
        return (
            "Namaste! Main CodeGuard AI Assistant hoon. "
            "Main aapki help kar sakta hoon:\n"
            "- Scan findings explain karna\n"
            "- Security vulnerabilities fix karna\n"
            "- Code review aur best practices\n"
            "- GitHub/Google OAuth issues\n"
            "- Backend/Frontend errors debug karna\n\n"
            "Apna code, error, ya scan result paste karo."
        )

    if any(word in text for word in ["scan", "finding", "vulnerability", "security", "risk", "semgrep", "gitleaks"]):
        return (
            "Scan findings ke liye:\n"
            "1. Sabse pehle HIGH/CRITICAL severity findings dekho\n"
            "2. Affected file aur line number check karo\n"
            "3. User input se data flow trace karo\n"
            "4. Input validation ya safer API use karo\n"
            "5. Fix ke baad dobara scan karo\n\n"
            "Specific finding paste karo, main detailed fix dunga."
        )

    if any(word in text for word in ["password", "jwt", "token", "auth", "login", "oauth", "github", "google"]):
        return (
            "Authentication best practices:\n"
            "- Passwords: bcrypt se hash karo (passlib use karo)\n"
            "- JWT: short-lived tokens (8 days max), SECRET_KEY strong rakho\n"
            "- OAuth: callback URLs sirf trusted domains pe set karo\n"
            "- Frontend mein secrets kabhi mat rakho\n"
            "- Private routes pe get_current_user dependency lagao\n\n"
            "GitHub/Google OAuth ke liye backend/.env mein credentials sahi hone chahiye."
        )

    if any(word in text for word in ["upload", "file", "scan upload", "zip", "code upload"]):
        return (
            "File upload flow CodeGuard mein:\n"
            "- /upload endpoint pe ZIP ya individual files bhejo\n"
            "- Scan automatically trigger hota hai upload ke baad\n"
            "- WebSocket /ws/scan-progress pe real-time progress milti hai\n"
            "- Results /scans aur /results pages pe dikhte hain\n\n"
            "Upload issue hai toh backend logs check karo."
        )

    if any(word in text for word in ["report", "pdf", "export", "download"]):
        return (
            "Reports CodeGuard mein:\n"
            "- Scan complete hone ke baad PDF report generate hoti hai\n"
            "- /api/v1/reports/{scan_id} se download karo\n"
            "- Report mein findings, severity, aur AI fix suggestions hote hain"
        )

    if any(word in text for word in ["fix", "bug", "error", "crash", "500", "404", "cors"]):
        return (
            "Debug karne ke liye:\n"
            "1. Error message aur stack trace share karo\n"
            "2. Konsa endpoint fail ho raha hai batao\n"
            "3. backend/server.log check karo\n"
            "4. CORS error hai toh BACKEND_CORS_ORIGINS mein frontend URL add karo\n\n"
            "Code snippet paste karo, main fix suggest karunga."
        )

    if any(word in text for word in ["team", "member", "invite", "project"]):
        return (
            "Teams aur Projects CodeGuard mein:\n"
            "- /teams page pe team banao aur members invite karo\n"
            "- Har project ke liye alag scans aur reports hote hain\n"
            "- Team members shared projects ke scans dekh sakte hain"
        )

    return (
        "Main CodeGuard AI Assistant hoon. Yeh topics pe help kar sakta hoon:\n"
        "- Security scan findings aur fixes\n"
        "- Authentication (JWT, OAuth, passwords)\n"
        "- Code upload aur scan workflow\n"
        "- PDF reports aur exports\n"
        "- Backend/Frontend errors\n"
        "- Teams aur project management\n\n"
        "Apna specific question ya code paste karo."
    )


@router.post("/", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Chat endpoint for the CodeGuard AI project assistant.
    """
    if not _is_project_related(request.message):
        return ChatResponse(reply=PROJECT_SCOPE_REPLY)

    ai_suggester = AISuggester()

    if not ai_suggester.api_key:
        return ChatResponse(reply=_local_assistant_reply(request.message))

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

## Tech Stack
- Backend: FastAPI (Python), SQLite/PostgreSQL, JWT auth
- Frontend: Next.js 16, TypeScript, Tailwind CSS, Zustand
- AI: OpenAI GPT-4o / Claude / Grok

## Mandatory Response Rules
1. Answer only CodeGuard AI project, code security, vulnerability, software development, debugging, and platform workflow questions.
2. If the user asks anything outside this project scope, refuse briefly and redirect them to CodeGuard topics.
3. Do not provide general knowledge, entertainment, politics, personal advice, or unrelated content.
4. Always give actionable, specific advice.
5. For vulnerability fixes, include corrected code snippets when enough code context is available.
6. Keep responses concise and structured with bullets or numbered steps.
7. If user shares code or error, analyze it in the context of this CodeGuard AI project.
8. Mention relevant CodeGuard features when applicable, such as scan results, reports, uploads, teams, or auth.

## Current User
Name: {current_user.full_name}
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
