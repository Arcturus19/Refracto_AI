# Production Hardening Log

## Entry: 2026-03-14

### Context
- Repository: Refracto_AI
- Branch: copilot/create-necessary-branches
- Scope: Security hardening, deployment safety, auth enforcement, frontend session safety, and validation fixes.

### Summary of Work Completed

#### 1. Backend authentication and authorization hardening
- Enforced authentication on previously open endpoints in:
  - backend/services/patient_service/main.py
  - backend/services/imaging_service/main.py
  - backend/services/ml_service/main.py
- Added service-level auth helper modules:
  - backend/services/patient_service/auth.py
  - backend/services/imaging_service/auth.py
  - backend/services/ml_service/auth.py
- Updated auth service token handling to support cookie-based access token extraction and stronger route protection in:
  - backend/services/auth_service/dependencies.py
  - backend/services/auth_service/main.py

#### 2. Privilege escalation prevention
- Removed user-submitted role assignment from registration flow in:
  - backend/services/auth_service/schemas.py
  - backend/services/auth_service/main.py
- Updated frontend registration flow to remove admin role selection:
  - frontend/src/pages/LoginPage.tsx

#### 3. Session security improvements (frontend)
- Reduced persistent auth token exposure by moving to in-memory token helper plus cookie-backed session pattern:
  - frontend/src/utils/authSession.ts
  - frontend/src/services/api.ts
  - frontend/src/store/useAuthStore.ts
- Added session expiry event handling and protected-route bootstrapping updates:
  - frontend/src/App.tsx
  - frontend/src/components/ProtectedRoute.tsx
- Updated logout behavior:
  - frontend/src/components/Header.tsx

#### 4. CORS and debug defaults
- Replaced wildcard CORS with env-driven origin configuration and safer debug defaults in:
  - backend/services/auth_service/config.py
  - backend/services/patient_service/config.py
  - backend/services/imaging_service/config.py
  - backend/services/ml_service/config.py
- Gated docs endpoints by debug mode in service apps.

#### 5. Login abuse mitigation
- Added in-memory rate limiting for login attempts in:
  - backend/services/auth_service/main.py

#### 6. Error leak reduction and upload input hardening
- Replaced internal exception leakage with generic client-facing errors while preserving server logs in:
  - backend/services/ml_service/main.py
  - backend/services/ml_service/xai_api_routes.py
  - backend/services/imaging_service/main.py
- Added upload validation and size enforcement pathways in ML/imaging services.

#### 7. Health/readiness reliability
- Implemented and aligned readiness behavior in ML service:
  - backend/services/ml_service/main.py
- Confirmed k8s probe alignment:
  - backend/kubernetes/ml-service-deployment.yaml

#### 8. DICOM internal service trust path
- Added internal token forwarding for service-to-service calls in:
  - backend/services/dicom_service/main.py
  - backend/services/dicom_service/config.py
- Switched AUTO_CREATE_PATIENTS default to safer value (false).

#### 9. Docker and compose hardening
- Removed dev-only uvicorn reload usage in production Dockerfiles.
- Added non-root runtime users in service images.
- Standardized ML image base version to Python 3.11.
- Updated compose wiring for safer env usage, health checks, and startup dependency behavior in:
  - backend/docker-compose.yml
  - backend/services/auth_service/Dockerfile
  - backend/services/patient_service/Dockerfile
  - backend/services/imaging_service/Dockerfile
  - backend/services/ml_service/Dockerfile
  - backend/services/dicom_service/Dockerfile

#### 10. Secret default cleanup
- Hardened example env values in:
  - backend/.env.example
- Removed default hardcoded MinIO fallback credentials from shared client path:
  - backend/shared/minio_client.py

#### 11. Frontend resilience and tooling updates
- Added app-level runtime crash boundary:
  - frontend/src/components/ErrorBoundary.tsx
- Added env-driven API/proxy support in Vite config:
  - frontend/vite.config.ts
- Updated dependencies and scripts for test/typecheck tooling in:
  - frontend/package.json
- Added ambient TS declarations required for current toolchain:
  - frontend/src/vite-env.d.ts

### Validation Performed
- Editor diagnostics check (`get_errors`) on key modified files: no reported errors.
- Frontend package install completed after dependency alignment.
- Frontend type-check completed successfully (`npm run typecheck`).
- Frontend test run executes, but existing component tests still have failing assertions unrelated to this document entry.

### Known Follow-up Items
- Rotate and verify real deployment secrets in live environment file(s).
- Add production-grade token revocation and refresh-token rotation.
- Resolve existing frontend test suite assertion failures.
- Continue replacing any documentation examples that still show weak sample credentials.

### Notes
- This log entry is intended as a baseline audit trail for ongoing production-readiness work.
- Future entries should append below with date, scope, validation status, and remaining risk.
