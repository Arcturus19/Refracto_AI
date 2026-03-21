# Test Cases - Refracto AI

Legend:
- Priority: P0 (critical), P1 (high), P2 (medium)
- Type: API, UI, Integration, Security, Data, Non-Functional

| ID | Area | Title | Preconditions | Steps | Expected Result | Type | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-001 | Auth | Register new user | Auth service running | 1) POST /register with valid email/password/name | User created, 201, returns user payload | API | P0 |
| AUTH-002 | Auth | Duplicate email registration blocked | User exists | 1) POST /register with same email | 400 with "Email already registered" | API | P0 |
| AUTH-003 | Auth | Login success | User exists | 1) POST /login valid credentials | 200, returns token and user | API | P0 |
| AUTH-004 | Auth | Login failure | User exists | 1) POST /login with wrong password | 401 with "Incorrect email or password" | API | P0 |
| AUTH-005 | Auth | Rate limiting on failed logins | None | 1) Fail login repeatedly > limit | 429 Too Many Requests | Security | P1 |
| AUTH-006 | Auth | Logout clears cookie | Logged in | 1) POST /logout | Cookie cleared, 200 | API | P1 |
| AUTH-007 | Auth | Get current user | Logged in | 1) GET /me | Returns user data | API | P0 |
| AUTH-008 | Auth | Update profile | Logged in | 1) PUT /me/profile with new name/email | Updated user returned | API | P1 |
| AUTH-009 | Auth | Update password | Logged in | 1) PUT /me/password | 200, password changed | API | P1 |
| AUTH-010 | Auth | Settings CRUD | Logged in | 1) GET /me/settings 2) PUT /me/settings | Settings saved/loaded | API | P2 |
| AUTH-011 | Auth | Admin list users | Admin user | 1) GET /admin/users | Returns users list | API | P1 |
| AUTH-012 | Auth | Non-admin blocked from admin users | Non-admin user | 1) GET /admin/users | 403 Forbidden | Security | P1 |

| PAT-001 | Patient | Create patient | Patient service running | 1) POST /patients valid payload | 201 and patient data | API | P0 |
| PAT-002 | Patient | List patients | Patient exists | 1) GET /patients | Returns list | API | P0 |
| PAT-003 | Patient | Search patients min length | Patient exists | 1) GET /patients?search=a | 400 invalid search | API | P2 |
| PAT-004 | Patient | Get patient by ID | Patient exists | 1) GET /patients/{id} | 200 with patient | API | P0 |
| PAT-005 | Patient | Update patient | Patient exists | 1) PUT /patients/{id} | Updated patient returned | API | P1 |
| PAT-006 | Patient | Delete patient | Patient exists | 1) DELETE /patients/{id} | 204 No Content | API | P1 |
| PAT-007 | Patient | Access control enforced | User without access | 1) GET /patients/{id} | 403 Forbidden | Security | P0 |
| PAT-008 | Patient | Stats summary | Patient exists | 1) GET /patients/stats/summary | Correct counts | API | P2 |
| PAT-009 | Patient | Grant access (admin) | Admin user | 1) POST /patients/{id}/access/grant | Access granted | Security | P1 |
| PAT-010 | Patient | Record consent | Access granted | 1) POST /patients/{id}/consents | Consent recorded | API | P1 |
| PAT-011 | Patient | Verify consent | Consent exists | 1) GET /patients/{id}/consents/verify | is_valid true | API | P1 |
| PAT-012 | Patient | Internal verify patient | Internal token set | 1) GET /internal/patients/{id}/verify | allowed true/false | Integration | P1 |
| PAT-013 | Patient | Internal list user patients | Internal token set | 1) GET /internal/users/{id}/patients | List patient IDs | Integration | P2 |

| IMG-001 | Imaging | Upload fundus image | Imaging + MinIO | 1) POST /upload/{patient_id} with jpg/png | 201 with image record | API | P0 |
| IMG-002 | Imaging | Upload DICOM | Imaging + MinIO | 1) POST /upload/{patient_id} with dcm | 201, stored, converted if possible | API | P0 |
| IMG-003 | Imaging | Reject unsupported type | Imaging running | 1) POST /upload with txt | 400 unsupported type | API | P1 |
| IMG-004 | Imaging | Oversized upload blocked | Imaging running | 1) POST /upload large file | 413 too large | API | P1 |
| IMG-005 | Imaging | Empty file blocked | Imaging running | 1) POST /upload empty | 400 empty file | API | P1 |
| IMG-006 | Imaging | Get patient images | Patient has images | 1) GET /images/{patient_id} | List with URLs | API | P0 |
| IMG-007 | Imaging | Filter by image type | Patient has both | 1) GET /images/{id}?image_type=OCT | Only OCT | API | P2 |
| IMG-008 | Imaging | Get image by ID | Image exists | 1) GET /image/{image_id} | Image record with URL | API | P1 |
| IMG-009 | Imaging | Delete image | Image exists | 1) DELETE /image/{image_id} | 204 and storage delete | API | P1 |
| IMG-010 | Imaging | Recent images | Images exist | 1) GET /images/recent?limit=1 | 1 most recent | API | P2 |
| IMG-011 | Imaging | Stats endpoint | Images exist | 1) GET /stats | Totals by type | API | P2 |
| IMG-012 | Imaging | Access control enforced | User no access | 1) GET /images/{patient_id} | 403 Forbidden | Security | P0 |

| DICOM-001 | DICOM | C-ECHO verification | DICOM service running | 1) Run echoscu | Verification accepted | Integration | P0 |
| DICOM-002 | DICOM | C-STORE receive DICOM | DICOM service running | 1) Send DICOM file | File saved to temp storage | Integration | P0 |
| DICOM-003 | DICOM | Auto-create patient | Patient service available | 1) Send DICOM with new patient | Patient created if enabled | Integration | P1 |
| DICOM-004 | DICOM | Auto-ingest to imaging | Imaging service available | 1) Send DICOM | Imaging upload triggered | Integration | P1 |
| DICOM-005 | DICOM | Invalid DICOM rejected | Service running | 1) Send malformed DICOM | Error logged, no crash | Resilience | P1 |

| ML-001 | ML | Health check | ML service running | 1) GET /health | Healthy + models_loaded | API | P0 |
| ML-002 | ML | Readiness check | ML models loaded | 1) GET /health/ready | 200 ready | API | P1 |
| ML-003 | ML | Predict pathology | ML running | 1) POST /predict/pathology with image | DR grade + glaucoma risk | API | P0 |
| ML-004 | ML | Predict refraction | ML running | 1) POST /predict/refraction with image | sphere/cylinder/axis | API | P0 |
| ML-005 | ML | Explain pathology | ML running | 1) POST /explain/pathology with image | Heatmap + explanation | API | P1 |
| ML-006 | ML | Invalid image rejected | ML running | 1) POST with invalid bytes | 400 invalid image | API | P1 |
| ML-007 | ML | Upload size limit enforced | ML running | 1) POST large file | 413 too large | API | P1 |
| ML-008 | ML | Consent required (mode required) | Consent required | 1) POST without patient_id | 400 patient_id required | Security | P1 |
| ML-009 | ML | Consent denied | Consent invalid | 1) POST with patient_id lacking consent | 403 denied | Security | P1 |
| ML-010 | ML | Internal verify error handling | Patient svc down | 1) POST with patient_id | 503 consent verification unavailable | Resilience | P1 |

| UI-001 | UI | Login form validation | Frontend running | 1) Open login 2) Submit empty | Required fields enforced | UI | P0 |
| UI-002 | UI | Register form validation | Frontend running | 1) Password < 8 | Error toast | UI | P1 |
| UI-003 | UI | Successful login flow | Backend running | 1) Login 2) Redirect to dashboard | Dashboard loads | UI | P0 |
| UI-004 | UI | Protected routes redirect | Not logged in | 1) Navigate to /patients | Redirect to /login | UI | P0 |
| UI-005 | UI | Dashboard polling | Backend running | 1) Wait for poll | New image toast | UI | P2 |
| UI-006 | UI | Logout flow | Logged in | 1) Trigger logout | Redirect to login | UI | P1 |
| UI-007 | UI | Patient list load | Logged in | 1) Open Patients | Table/list populated | UI | P1 |
| UI-008 | UI | Image upload UI | Logged in | 1) Upload image | Success message | UI | P1 |
| UI-009 | UI | Analysis flow | Logged in | 1) Upload + analyze | Results render | UI | P0 |
| UI-010 | UI | Error boundary | Simulated error | 1) Force error | Friendly error view | UI | P2 |

| INT-001 | Integration | Auth -> Patient access | All services running | 1) Login 2) Create patient 3) List | Access limited to owner | Integration | P0 |
| INT-002 | Integration | DICOM -> Imaging upload | DICOM + Imaging running | 1) Send DICOM 2) Verify imaging record | Image stored and retrievable | Integration | P0 |
| INT-003 | Integration | Imaging -> ML workflow | Imaging + ML running | 1) Upload 2) Analyze | Predictions available | Integration | P0 |
| INT-004 | Integration | MinIO object retrieval | MinIO running | 1) Fetch presigned URL | File accessible | Integration | P1 |
| INT-005 | Integration | Internal token auth | Internal token set | 1) Call internal endpoints | Works only with token | Security | P1 |

| SEC-001 | Security | JWT required for API | Services running | 1) Call protected endpoint without token | 401 Unauthorized | Security | P0 |
| SEC-002 | Security | Token expiry | Auth running | 1) Use expired token | 401 Unauthorized | Security | P1 |
| SEC-003 | Security | CORS origins limited | Services running | 1) Request from disallowed origin | Blocked by CORS | Security | P2 |
| SEC-004 | Security | File name sanitization | Imaging upload | 1) Upload filename with path chars | Stored safely | Security | P2 |

| NF-001 | Non-Functional | Startup time | Docker running | 1) Start compose | All services healthy < 2 min | Non-Functional | P2 |
| NF-002 | Non-Functional | Basic load | Backend running | 1) 20 concurrent /health | No errors, stable | Non-Functional | P2 |
