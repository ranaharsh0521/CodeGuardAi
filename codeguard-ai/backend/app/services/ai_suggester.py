import httpx
from typing import Dict, Any, Optional
from app.core.config import settings


CHAT_SYSTEM_PROMPT = (
    "You are CodeGuard AI, the project assistant for the CodeGuard AI platform. "
    "Only answer questions about this platform, code security, vulnerabilities, "
    "software development, debugging, auth, scans, reports, uploads, teams, and "
    "the project's backend/frontend workflow. If the request is unrelated, refuse "
    "briefly and redirect the user to CodeGuard AI topics. Be concise, specific, "
    "and actionable."
)


class AISuggester:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.api_key = settings.AI_API_KEY

    async def get_chat_response(self, prompt: str) -> str:
        """Return a plain-text reply for the chat assistant (no EXPLANATION/FIX parsing)."""
        if not self.api_key:
            return ""

        try:
            if self.provider == "claude":
                return await self._raw_claude(prompt)
            elif self.provider == "openai":
                return await self._raw_openai(prompt)
            else:
                return await self._raw_grok(prompt)
        except Exception as e:
            raise RuntimeError(f"AI chat request failed: {e}") from e

    async def _raw_openai(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": CHAT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1024,
            "temperature": 0.3,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

    async def _raw_claude(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 1024,
            "system": CHAT_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"].strip()

    async def _raw_grok(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "grok-beta",
            "messages": [
                {
                    "role": "system",
                    "content": CHAT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

    async def get_fix_suggestion(self, finding: Dict[str, Any]) -> Dict[str, str]:
        """
        Calls the LLM to get a fix suggestion and explanation.
        """
        if not self.api_key:
            return {
                "ai_fix_suggestion": "AI integration not configured (API key missing).",
                "ai_explanation": ""
            }

        prompt = self._build_prompt(finding)

        try:
            if self.provider == "claude":
                return await self._call_claude(prompt)
            elif self.provider == "openai":
                return await self._call_openai(prompt)
            else:
                return await self._call_grok(prompt)
        except Exception as e:
            return {
                "ai_fix_suggestion": f"Failed to get AI suggestion: {str(e)}",
                "ai_explanation": ""
            }

    def _build_prompt(self, finding: Dict[str, Any]) -> str:
        return f"""
You are an expert security engineer and developer.
A vulnerability or bug was found in the codebase.
Tool: {finding.get('tool')}
Rule ID: {finding.get('rule_id')}
Message: {finding.get('message')}
Code Snippet:
```
{finding.get('code_snippet', 'N/A')}
```
Provide two things in your response:
1. A clear explanation of why this is a problem and the potential risk.
2. The patched code snippet that fixes the issue (provide a unified diff format if possible, or just the complete corrected block).

Respond in the following format exactly:
EXPLANATION:
[Your explanation here]

FIX:
[Your patched code here]
"""

    async def _call_openai(self, prompt: str) -> Dict[str, str]:
        """Call OpenAI ChatGPT API (gpt-4o)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "You are CodeGuard AI, an expert software security engineer. Help developers find and fix security vulnerabilities."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_ai_response(text)

    async def _call_claude(self, prompt: str) -> Dict[str, str]:
        """Call Anthropic Claude API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            text = data["content"][0]["text"]
            return self._parse_ai_response(text)

    async def _call_grok(self, prompt: str) -> Dict[str, str]:
        """Call xAI Grok API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-beta",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_ai_response(text)

    def _parse_ai_response(self, text: str) -> Dict[str, str]:
        parts = text.split("FIX:")
        explanation = parts[0].replace("EXPLANATION:", "").strip()
        fix = parts[1].strip() if len(parts) > 1 else ""
        return {
            "ai_explanation": explanation,
            "ai_fix_suggestion": fix
        }
