# CodeGuard AI - TODO

## Backend: Missing scan feature
- [x] Add background scan runner that uses existing `AnalyzerService` + `SecurityScanner`/`SecretDetector`.

- [ ] Persist scan status/progress + findings + risk_score to `ScanResult`.
- [ ] Wire scan runner into `POST /api/v1/scans/` endpoint.
- [ ] Add/adjust status endpoint to reflect real progress and completion.

## Development ergonomics
- [ ] Ensure scan runner works without Celery/Redis (dev fallback).
- [ ] Add minimal directory handling so analyzers run against the cloned repo or a local workspace path.

## Verification
- [ ] Start backend and hit `/health`.
- [ ] Register/login, create a project, trigger scan, and verify `/api/v1/scans/{id}` returns findings.
