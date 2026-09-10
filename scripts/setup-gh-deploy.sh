#!/usr/bin/env bash
#
# One-time setup: let GitHub Actions deploy to Cloud Run *keylessly* via
# Workload Identity Federation (no service-account key stored in GitHub).
# Safe to re-run (idempotent). Run from anywhere; needs gcloud + gh authenticated.
#
set -euo pipefail

PROJECT_ID="personal-digital-twin-508403"
REGION="us-central1"
REPO="sridharchilukuri/personal-digital-twin"
POOL="github-pool"
PROVIDER="github-provider"
SA_NAME="github-deployer"

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "▸ Enabling required APIs (idempotent)…"
gcloud services enable iamcredentials.googleapis.com sts.googleapis.com --project "$PROJECT_ID"

echo "▸ Creating deploy service account (if missing)…"
gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="GitHub Actions deployer" --project "$PROJECT_ID"

echo "▸ Granting deploy roles to the service account…"
for role in \
  roles/run.admin \
  roles/cloudbuild.builds.editor \
  roles/artifactregistry.admin \
  roles/storage.admin \
  roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$role" --condition=None >/dev/null
done

echo "▸ Letting the deploy SA act as the Cloud Run runtime service account…"
gcloud iam service-accounts add-iam-policy-binding \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/iam.serviceAccountUser" >/dev/null

echo "▸ Creating Workload Identity pool + GitHub OIDC provider (if missing)…"
gcloud iam workload-identity-pools describe "$POOL" --location=global >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools create "$POOL" \
    --location=global --display-name="GitHub pool"

gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --location=global --workload-identity-pool="$POOL" >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
    --location=global --workload-identity-pool="$POOL" \
    --display-name="GitHub provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition="assertion.repository=='${REPO}'" \
    --issuer-uri="https://token.actions.githubusercontent.com"

POOL_NAME="$(gcloud iam workload-identity-pools describe "$POOL" \
  --location=global --format='value(name)')"
PROVIDER_NAME="$(gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --location=global --workload-identity-pool="$POOL" --format='value(name)')"

echo "▸ Allowing ONLY this repo to impersonate the deploy SA…"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/${REPO}" >/dev/null

echo "▸ Saving values as GitHub repo variables (not secrets — none are sensitive)…"
gh variable set GCP_PROJECT_ID   --repo "$REPO" --body "$PROJECT_ID"
gh variable set GCP_REGION       --repo "$REPO" --body "$REGION"
gh variable set GCP_WIF_PROVIDER --repo "$REPO" --body "$PROVIDER_NAME"
gh variable set GCP_DEPLOY_SA    --repo "$REPO" --body "$SA_EMAIL"

echo
echo "✓ Keyless deploy is wired up."
echo "  Provider : $PROVIDER_NAME"
echo "  Deploy SA: $SA_EMAIL"
echo "  Push to main and the Deploy workflow will run. No secrets stored in GitHub."
