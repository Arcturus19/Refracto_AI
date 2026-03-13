# Refracto AI — Branching Strategy

**Project**: Hybrid XAI Clinical Decision Support System for Integrated Ophthalmic Care  
**Student**: K.M.P. Jayalath (IT_IFLS_001/B003/0020)  
**Repository**: `git@github.com:Arcturus19/Refracto_AI.git`

---

## Branch Overview

The repository follows a **Git Flow**-inspired branching model with three long-lived branches and short-lived feature branches aligned to the 3-phase implementation roadmap.

```
main ──────────────────────────────────────────────────────→  (production-ready)
  └── develop ───────────────────────────────────────────→  (integration branch)
        ├── feature/phase1/p0.1-multimodal-fusion
        ├── feature/phase1/p0.2-refracto-link
        ├── feature/phase1/p0.3-multimodal-ingestion
        ├── feature/phase1/p0.4-local-data-manager
        ├── feature/phase1/p0.5-clinical-concordance
        ├── feature/phase1/p0.6-audit-trail
        ├── feature/phase1/p0.7-db-migration
        ├── feature/phase1/p0.8-secrets-management
        ├── feature/phase1/p0.9-consent-ui
        ├── feature/phase2/p1.1-structured-data
        ├── feature/phase2/p1.2-label-harmonization
        ├── feature/phase2/p1.3-shap-integration
        ├── feature/phase2/p1.4-nl-reports
        ├── feature/phase2/p1.5-training-pipeline
        ├── feature/phase2/p1.6-evaluation-metrics
        ├── feature/phase2/p1.7-uncertainty-quantification
        ├── feature/phase2/p1.8-clinician-feedback
        ├── feature/phase3/p2.1-xai-dashboard
        ├── feature/phase3/p2.2-bias-monitoring
        ├── feature/phase3/p2.3-data-quality
        ├── feature/phase3/p2.4-cohort-stratification
        ├── feature/phase3/p2.5-model-registry
        ├── release/v1.0    (Phase 1 release)
        ├── release/v2.0    (Phase 2 release)
        ├── release/v3.0    (Phase 3 release)
        └── hotfix/*        (production bug fixes)
```

---

## Branch Descriptions

### Long-Lived Branches

| Branch    | Purpose                                    | Protected | Merge From        |
|-----------|--------------------------------------------|-----------|-------------------|
| `main`    | Production-ready, tagged releases only     | ✅ Yes    | `release/*`, `hotfix/*` |
| `develop` | Integration branch; all features merge here | ✅ Yes   | `feature/**`      |

### Short-Lived Branches

| Pattern               | Purpose                                      | Merges To  |
|-----------------------|----------------------------------------------|------------|
| `feature/phase1/pX.X-*` | Phase 1 critical foundation features      | `develop`  |
| `feature/phase2/pX.X-*` | Phase 2 core features                     | `develop`  |
| `feature/phase3/pX.X-*` | Phase 3 enhancement features              | `develop`  |
| `release/vX.Y`        | Release candidate preparation               | `main` + `develop` |
| `hotfix/issue-*`      | Emergency production bug fixes              | `main` + `develop` |

---

## Phase 1 Feature Branches (Weeks 1–4)

| Branch                                      | Feature                          | Status   |
|---------------------------------------------|----------------------------------|----------|
| `feature/phase1/p0.1-multimodal-fusion`     | Multi-Modal Fusion (MTL)        | ✅ Done  |
| `feature/phase1/p0.2-refracto-link`         | Refracto-Pathological Link       | ✅ Done  |
| `feature/phase1/p0.3-multimodal-ingestion`  | Multi-Modal Data Ingestion       | ✅ Done  |
| `feature/phase1/p0.4-local-data-manager`    | Local Patient Data Manager       | ✅ Done  |
| `feature/phase1/p0.5-clinical-concordance`  | Clinical Concordance (CCR)       | ✅ Done  |
| `feature/phase1/p0.6-audit-trail`           | Ethical Audit Trail              | ✅ Done  |
| `feature/phase1/p0.7-db-migration`          | Database Schema Migration        | ✅ Done  |
| `feature/phase1/p0.8-secrets-management`    | Secrets Management (Vault)       | ✅ Done  |
| `feature/phase1/p0.9-consent-ui`            | Consent & Privacy UI             | ✅ Done  |

---

## Phase 2 Feature Branches (Weeks 5–8)

| Branch                                        | Feature                          | Status      |
|-----------------------------------------------|----------------------------------|-------------|
| `feature/phase2/p1.1-structured-data`         | Structured Data Integration (GBM) | 🔲 Pending |
| `feature/phase2/p1.2-label-harmonization`     | Label Harmonization Engine       | 🔲 Pending  |
| `feature/phase2/p1.3-shap-integration`        | SHAP Post-Hoc Explainability     | 🔲 Pending  |
| `feature/phase2/p1.4-nl-reports`              | Natural Language Report Gen      | 🔲 Pending  |
| `feature/phase2/p1.5-training-pipeline`       | Multi-Stage Training Pipeline    | 🔲 Pending  |
| `feature/phase2/p1.6-evaluation-metrics`      | Comprehensive Evaluation Metrics | 🔲 Pending  |
| `feature/phase2/p1.7-uncertainty-quantification` | Uncertainty Quantification    | 🔲 Pending  |
| `feature/phase2/p1.8-clinician-feedback`      | Clinician Feedback Loop          | 🔲 Pending  |

---

## Phase 3 Feature Branches (Weeks 9–12)

| Branch                                        | Feature                          | Status      |
|-----------------------------------------------|----------------------------------|-------------|
| `feature/phase3/p2.1-xai-dashboard`           | XAI Dashboard                    | 🔲 Pending  |
| `feature/phase3/p2.2-bias-monitoring`         | Bias & Fairness Monitoring       | 🔲 Pending  |
| `feature/phase3/p2.3-data-quality`            | Data Quality & Curation          | 🔲 Pending  |
| `feature/phase3/p2.4-cohort-stratification`   | Cohort Stratification            | 🔲 Pending  |
| `feature/phase3/p2.5-model-registry`          | Model Registry & Versioning      | 🔲 Pending  |

---

## Workflow Rules

### Opening a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/phase1/p0.X-feature-name
```

### Merging a Feature Branch

1. Ensure all CI checks pass on the feature branch
2. Open a Pull Request targeting `develop`
3. Require at least 1 code review approval
4. Squash-merge into `develop`
5. Delete the feature branch after merge

### Creating a Release

```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.0
# Bump version, update CHANGELOG
git push origin release/v1.0
# Open PR to main → merge → tag
git tag v1.0.0
git push origin v1.0.0
# Back-merge into develop
git checkout develop
git merge release/v1.0
git push origin develop
```

### Hotfix Workflow

```bash
git checkout main
git pull origin main
git checkout -b hotfix/issue-<number>-short-description
# Fix the bug
git push origin hotfix/issue-<number>-short-description
# Open PRs to both main and develop
```

---

## Branch Naming Conventions

| Type     | Pattern                          | Example                                      |
|----------|----------------------------------|----------------------------------------------|
| Feature  | `feature/<phase>/<id>-<slug>`    | `feature/phase1/p0.1-multimodal-fusion`      |
| Release  | `release/v<major>.<minor>`       | `release/v1.0`                               |
| Hotfix   | `hotfix/issue-<num>-<slug>`      | `hotfix/issue-42-fix-null-prediction`        |
| Bugfix   | `bugfix/<id>-<slug>`             | `bugfix/p0.3-coregistration-crash`           |

---

## CI/CD Pipeline per Branch

| Branch        | Backend CI | Frontend CI | Docker Build | Deploy Staging | Deploy Prod |
|---------------|:----------:|:-----------:|:------------:|:--------------:|:-----------:|
| `feature/**`  | ✅         | ✅          | ✅           | ❌             | ❌          |
| `develop`     | ✅         | ✅          | ✅           | ✅             | ❌          |
| `release/**`  | ✅         | ✅          | ✅           | ✅             | ❌          |
| `main`        | ✅         | ✅          | ✅           | ✅             | ✅          |
| `hotfix/**`   | ✅         | ✅          | ✅           | ✅             | ✅          |

---

## Quick-Start: Create All Feature Branches Locally

Run the helper script to create all necessary feature branches off of `develop`:

```bash
chmod +x scripts/create-branches.sh
./scripts/create-branches.sh
```

See [`scripts/create-branches.sh`](scripts/create-branches.sh) for the full branch list.

---

## Branch Protection Rules (Recommended Settings)

Configure the following in GitHub → Settings → Branches:

### `main`
- ✅ Require a pull request before merging
- ✅ Require approvals: **2**
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
  - `Backend CI / Lint & Test (auth_service)`
  - `Backend CI / Lint & Test (ml_service)`
  - `Frontend CI / Lint & TypeCheck`
  - `Frontend CI / Production Build`
- ✅ Require branches to be up to date before merging
- ✅ Do not allow bypassing the above settings

### `develop`
- ✅ Require a pull request before merging
- ✅ Require approvals: **1**
- ✅ Require status checks to pass before merging
  - `Backend CI / Lint & Test (ml_service)`
  - `Frontend CI / Lint & TypeCheck`
- ✅ Require branches to be up to date before merging
