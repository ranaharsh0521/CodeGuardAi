#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeGuard AI -- End-to-End Backend Verification Script
Run after starting the backend to confirm all APIs work.

Usage:
    cd backend
    python verify_backend.py
"""

import sys
import time

try:
    import httpx
except ImportError:
    print("Please install httpx:  pip install httpx")
    sys.exit(1)

BASE = "http://localhost:8000/api/v1"
ROOT = "http://localhost:8000"

_TS = str(int(time.time()))[-6:]
TEST_EMAIL    = f"verify{_TS}@example.com"
TEST_PASSWORD = "VerifyPass123!"
TEST_NAME     = f"Verify User {_TS}"


def ok(label: str, detail: str = "") -> None:
    line = f"[PASS] {label}"
    if detail:
        line += f"  => {detail}"
    print(line)


def fail(label: str, detail: str = "") -> None:
    line = f"[FAIL] {label}"
    if detail:
        line += f"  => {detail}"
    print(line)
    sys.exit(1)


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        ok(label, detail)
    else:
        fail(label, detail)


def main() -> None:
    print()
    print("=" * 50)
    print("  CodeGuard AI -- Backend Verification")
    print("=" * 50)
    print()

    client = httpx.Client(timeout=30)

    # 1. Health check
    r = client.get(f"{ROOT}/health")
    check("GET /health => 200", r.status_code == 200)
    health = r.json()
    print(f"   Project: {health.get('project')}  version: {health.get('version')}")
    print(f"   Demo findings enabled: {health.get('features', {}).get('demo_findings')}")

    # 2. Register
    r = client.post(f"{BASE}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME,
    })
    check("POST /auth/register => 200", r.status_code == 200, r.text[:100])

    # 3. Login
    r = client.post(f"{BASE}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    check("POST /auth/login => 200", r.status_code == 200)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   Token prefix: {token[:20]}...")

    # 4. Current user
    r = client.get(f"{BASE}/users/me", headers=headers)
    check("GET /users/me => 200", r.status_code == 200, r.json().get("email"))

    # 5. Create project (no repo URL => demo findings)
    r = client.post(f"{BASE}/projects/", json={
        "name": f"Test Project {_TS}",
        "description": "Automated verification project",
    }, headers=headers)
    check("POST /projects/ => 200", r.status_code == 200, r.text[:80])
    project_id = r.json()["id"]
    print(f"   Project ID: {project_id}")

    # 6. Trigger scan
    r = client.post(f"{BASE}/scans/", json={"project_id": project_id}, headers=headers)
    check("POST /scans/ => 200", r.status_code == 200, r.text[:120])
    scan = r.json()
    scan_id = scan["id"]
    print(f"   Scan ID: {scan_id}  initial status: {scan['status']}")
    check("scan.findings_count is int", isinstance(scan.get("findings_count"), int))
    check("scan.project_name present", bool(scan.get("project_name")))

    # 7. Poll scan status until done (up to 90 s)
    print(f"   Polling /scans/{scan_id}/status ...")
    terminal = {"completed", "failed"}
    deadline = time.time() + 90
    last_status = scan["status"]
    while time.time() < deadline:
        time.sleep(2)
        r = client.get(f"{BASE}/scans/{scan_id}/status", headers=headers)
        check(f"GET /scans/{scan_id}/status => 200", r.status_code == 200)
        s = r.json()
        last_status = s["status"]
        print(f"   status={last_status}  progress={s.get('progress')}%  msg={s.get('message')}")
        if last_status in terminal:
            break

    check(f"Scan reached terminal state (got '{last_status}')", last_status in terminal)

    # 8. Full scan detail
    r = client.get(f"{BASE}/scans/{scan_id}", headers=headers)
    check("GET /scans/{id} => 200", r.status_code == 200)
    detail = r.json()
    findings = detail.get("findings", [])
    risk_score = detail.get("risk_score", -1)
    check("findings is a list", isinstance(findings, list), f"{len(findings)} findings")
    check("risk_score >= 0", isinstance(risk_score, int) and risk_score >= 0, str(risk_score))

    # 9. List scans
    r = client.get(f"{BASE}/scans/", headers=headers)
    check("GET /scans/ => 200", r.status_code == 200)
    all_scans = r.json()
    check("scan appears in list", any(s["id"] == scan_id for s in all_scans))

    # 10. Logout
    r = client.post(f"{BASE}/auth/logout", json={}, headers=headers)
    check("POST /auth/logout => 200", r.status_code == 200)

    print()
    print("=" * 50)
    print("  ALL CHECKS PASSED")
    print(f"  status={last_status}  risk_score={risk_score}  findings={len(findings)}")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
