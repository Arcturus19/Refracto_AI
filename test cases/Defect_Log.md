# Defect Log - Refracto AI (Static Review)

This log captures potential defects and risks identified by static review only. Execution-based validation was not performed.

| ID | Severity | Area | Description | Evidence | Status |
| --- | --- | --- | --- | --- | --- |
| DEF-001 | High | Imaging Service | DICOM conversion uses file.filename.rsplit without guarding None, which can raise AttributeError for clients that omit filename in multipart upload. | [backend/services/imaging_service/main.py](backend/services/imaging_service/main.py) | Open |
| DEF-002 | Medium | Imaging Service | SQLAlchemy func import is placed at bottom of file after use; this is brittle and can confuse tooling or static analysis. | [backend/services/imaging_service/main.py](backend/services/imaging_service/main.py) | Open |
| DEF-003 | Medium | Frontend | Auth token stored only in memory; refresh clears token and relies on cookie. If cookies are blocked, all API calls will fail after refresh. | [frontend/src/utils/authSession.ts](frontend/src/utils/authSession.ts) | Open |
| DEF-004 | Medium | Frontend/API | API base URLs default to /api/* and require proxy in dev or reverse-proxy in prod. If not configured, all API calls return 404. | [frontend/vite.config.ts](frontend/vite.config.ts) | Open |
| DEF-005 | Medium | Imaging Service | DICOM conversion falls back silently on failure, but still stores original DICOM content with content_type possibly unchanged, leading to UI consumers expecting image/png. | [backend/services/imaging_service/main.py](backend/services/imaging_service/main.py) | Open |
