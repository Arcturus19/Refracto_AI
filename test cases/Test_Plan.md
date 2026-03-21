# Test Plan - Refracto AI

## 1. Objective
Validate the end-to-end system (frontend, backend microservices, ML services, DICOM ingestion, storage) for correctness, reliability, security, and user workflows.

## 2. Scope
In scope:
- Auth service (registration, login, profile, settings, admin user listing)
- Patient service (CRUD, access control, consent, internal verification)
- Imaging service (upload, validation, DICOM conversion, retrieval, stats, delete)
- DICOM service (C-ECHO, C-STORE, storage, auto-ingest integration)
- ML service (analysis, predictions, explainability, consent enforcement)
- Frontend UI and API integration
- Docker-compose and local runtime smoke checks

Out of scope:
- Real device integration (fundus/OCT hardware)
- Regulatory validation (HIPAA/FDA) beyond QA checks
- Full performance benchmarking on production hardware

## 3. Test Types
- Smoke tests
- Functional API tests
- UI functional tests
- Data validation tests
- Security and authz tests
- Error handling and resilience tests
- Integration tests across services
- Non-functional (basic performance, stability)

## 4. Environment
- OS: Windows
- Backend: Docker Compose
- Frontend: Vite dev server
- Database: Postgres (container)
- Object storage: MinIO

## 5. Test Data
- Valid and invalid user accounts
- Sample DICOM files and PNG/JPEG images
- Mock patient records and consent entries

## 6. Risks and Focus Areas
- Auth token handling and session invalidation
- Internal service access using internal tokens
- DICOM conversion and file validation
- ML endpoints with large uploads and invalid images
- Cross-service latency and error propagation

## 7. Entry/Exit Criteria
Entry:
- Services configured and runnable
- Environment variables set

Exit:
- All P0/P1 tests executed
- All critical defects documented

## 8. Execution Notes
This plan assumes both manual and API-based validation. If execution is not performed, results will be logged as "Not Run" with coverage recorded.
