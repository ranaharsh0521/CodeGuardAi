import smtplib
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings


class EmailService:
    def is_configured(self) -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)

    def send_scan_complete(
        self,
        to_email: str,
        project_name: str,
        scan_id: int,
        status: str,
        risk_score: int,
        findings_count: int,
    ) -> bool:
        if not self.is_configured():
            return False

        subject = f"[CodeGuard AI] Scan {status}: {project_name}"
        body = f"""
Your scheduled security scan has finished.

Project: {project_name}
Scan ID: {scan_id}
Status: {status}
Risk Score: {risk_score}/100
Findings: {findings_count}

View results: {settings.FRONTEND_URL}/results/{scan_id}
"""
        return self._send(to_email, subject, body.strip())

    def send_team_invite(self, to_email: str, team_name: str, inviter_name: str) -> bool:
        if not self.is_configured():
            return False
        subject = f"[CodeGuard AI] You've been invited to team '{team_name}'"
        body = f"""
{inviter_name} invited you to collaborate on CodeGuard AI team "{team_name}".

Sign up or log in at {settings.FRONTEND_URL} using this email address ({to_email}),
then open the Teams page to see your invitation.
"""
        return self._send(to_email, subject, body.strip())

    def _send(self, to_email: str, subject: str, body: str) -> bool:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False
