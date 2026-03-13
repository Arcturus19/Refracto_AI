#!/usr/bin/env bash
# =============================================================================
# create-branches.sh — Create all Refracto AI feature branches from develop
# =============================================================================
# Usage:
#   chmod +x scripts/create-branches.sh
#   ./scripts/create-branches.sh
#
# This script:
#   1. Ensures 'develop' exists (creates it from main if needed)
#   2. Creates all Phase 1, Phase 2, and Phase 3 feature branches
#   3. Pushes every branch to origin
#
# Prerequisites:
#   - Git remote 'origin' must be configured:
#       git remote add origin git@github.com:Arcturus19/Refracto_AI.git
#   - You must have push access to the repository
# =============================================================================

set -euo pipefail

REMOTE="origin"
BASE_BRANCH="develop"

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERR]${NC}   $*"; exit 1; }

# ── Preflight checks ──────────────────────────────────────────────────────────
command -v git >/dev/null 2>&1 || error "git is not installed."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
  error "Not inside a git repository. Run from the repo root."

info "Fetching latest from $REMOTE …"
git fetch "$REMOTE" --prune --quiet

# ── Ensure 'develop' exists ───────────────────────────────────────────────────
if git show-ref --verify --quiet "refs/remotes/$REMOTE/$BASE_BRANCH"; then
  info "'$BASE_BRANCH' already exists on $REMOTE — checking it out."
  git checkout "$BASE_BRANCH" 2>/dev/null || \
    git checkout -b "$BASE_BRANCH" --track "$REMOTE/$BASE_BRANCH"
  git pull "$REMOTE" "$BASE_BRANCH" --quiet
else
  info "Creating '$BASE_BRANCH' from $REMOTE/main …"
  git checkout -b "$BASE_BRANCH" "$REMOTE/main"
  git push "$REMOTE" "$BASE_BRANCH"
  success "'$BASE_BRANCH' created and pushed."
fi

# ── Branch definitions ────────────────────────────────────────────────────────
# Format: "branch-name|description"
BRANCHES=(
  # ── Phase 1: Critical Foundations (Weeks 1–4) ──────────────────────────────
  "feature/phase1/p0.1-multimodal-fusion|P0.1: Multi-Modal Fusion Architecture (MTL)"
  "feature/phase1/p0.2-refracto-link|P0.2: Refracto-Pathological Link Module"
  "feature/phase1/p0.3-multimodal-ingestion|P0.3: Multi-Modal Data Ingestion Pipeline"
  "feature/phase1/p0.4-local-data-manager|P0.4: Sri Lankan Local Patient Data Manager"
  "feature/phase1/p0.5-clinical-concordance|P0.5: Clinical Concordance (CCR) Framework"
  "feature/phase1/p0.6-audit-trail|P0.6: Ethical Audit Trail & Immutable Logging"
  "feature/phase1/p0.7-db-migration|P0.7: Database Schema Migration (Phase 1)"
  "feature/phase1/p0.8-secrets-management|P0.8: Secrets Management (Vault integration)"
  "feature/phase1/p0.9-consent-ui|P0.9: Consent & Privacy UI (React)"

  # ── Phase 2: Core Features (Weeks 5–8) ────────────────────────────────────
  "feature/phase2/p1.1-structured-data|P1.1: Structured Data Integration (Gradient Boosting)"
  "feature/phase2/p1.2-label-harmonization|P1.2: Label Harmonization Engine"
  "feature/phase2/p1.3-shap-integration|P1.3: SHAP Post-Hoc Explainability"
  "feature/phase2/p1.4-nl-reports|P1.4: Natural Language Report Generation"
  "feature/phase2/p1.5-training-pipeline|P1.5: Multi-Stage Training Pipeline"
  "feature/phase2/p1.6-evaluation-metrics|P1.6: Comprehensive Evaluation Metrics Framework"
  "feature/phase2/p1.7-uncertainty-quantification|P1.7: Uncertainty Quantification Module"
  "feature/phase2/p1.8-clinician-feedback|P1.8: Clinician Feedback Loop"

  # ── Phase 3: Enhancement & Polish (Weeks 9–12) ───────────────────────────
  "feature/phase3/p2.1-xai-dashboard|P2.1: XAI Dashboard (Grad-CAM + SHAP visualisation)"
  "feature/phase3/p2.2-bias-monitoring|P2.2: Bias & Fairness Monitoring"
  "feature/phase3/p2.3-data-quality|P2.3: Data Quality & Curation Pipeline"
  "feature/phase3/p2.4-cohort-stratification|P2.4: Cohort Stratification"
  "feature/phase3/p2.5-model-registry|P2.5: Model Registry & Versioning"

  # ── Release branches ──────────────────────────────────────────────────────
  "release/v1.0|Phase 1 release candidate"
  "release/v2.0|Phase 2 release candidate"
  "release/v3.0|Phase 3 release candidate"
)

# ── Create / push each branch ─────────────────────────────────────────────────
CREATED=0
SKIPPED=0

for entry in "${BRANCHES[@]}"; do
  branch="${entry%%|*}"
  desc="${entry##*|}"

  if git show-ref --verify --quiet "refs/remotes/$REMOTE/$branch"; then
    warn "Branch '$branch' already exists on $REMOTE — skipping."
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  info "Creating '$branch' ($desc) …"
  git checkout -b "$branch" "$BASE_BRANCH" --quiet
  git push "$REMOTE" "$branch" --quiet
  git checkout "$BASE_BRANCH" --quiet
  success "Pushed '$branch'"
  CREATED=$((CREATED + 1))
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Branch setup complete!${NC}"
echo -e "${GREEN}  Created : $CREATED branch(es)${NC}"
echo -e "${YELLOW}  Skipped : $SKIPPED branch(es) (already exist)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "All branches:"
git --no-pager branch -r | grep -v 'HEAD' | sort
