# Deploy — Google Cloud Run

How to put the twin on a public HTTPS URL. Target: **Google Cloud Run** (a scale-to-zero
container) with the API key in **Secret Manager**. Idle cost ≈ **$0**; you pay only for LLM
tokens.

Replace `PROJECT_ID` and `YOUR_LLM_KEY` below with your values.

---

## Phase 0 — One-time setup (~20 min, first time only)

1. **Create a Google Cloud project** at <https://console.cloud.google.com> → note its
   `PROJECT_ID`.
2. **Enable billing** on the project (a card is required, but you stay within the free tier).
   Set a **budget alert** (~$5) in Billing → Budgets for peace of mind.
3. **Install the CLI** (macOS):
   ```bash
   brew install --cask google-cloud-sdk
   ```
4. **Authenticate and select the project:**
   ```bash
   gcloud auth login
   gcloud config set project PROJECT_ID
   ```
5. **Enable the services we use:**
   ```bash
   gcloud services enable \
     run.googleapis.com \
     secretmanager.googleapis.com \
     cloudbuild.googleapis.com \
     artifactregistry.googleapis.com
   ```

## Phase 1 — Store the API key in Secret Manager (once per key)

```bash
# create the secret from your key (no trailing newline)
printf 'YOUR_LLM_KEY' | gcloud secrets create LLM_API_KEY --data-file=-

# let Cloud Run's runtime service account read it
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding LLM_API_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Phase 2 — Deploy

From the repo root:

```bash
gcloud run deploy digital-twin \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars=LLM_PROVIDER=openai,LLM_MODEL=gpt-4o \
  --set-secrets=LLM_API_KEY=LLM_API_KEY:latest
```

What each flag does:
- `--source .` — Cloud Build builds the image from the `Dockerfile` (no manual push).
- `--allow-unauthenticated` — makes the site **publicly accessible**.
- `--set-env-vars` — provider + model. `gpt-4o` (or Claude) is more reliable than `gpt-4o-mini`.
- `--set-secrets` — injects the key from Secret Manager as `LLM_API_KEY` (never in the image).

On success it prints a public URL like `https://digital-twin-xxxxxxxx-uc.a.run.app`.

## Phase 3 — Verify

1. Open the URL. Ask a grounded question ("What is Sridhar most proud of?") and an off-topic
   one ("what is 1+1?") — expect a real answer and a polite decline, respectively.
2. If something's off, read the logs:
   ```bash
   gcloud run services logs read digital-twin --region us-central1 --limit 50
   ```

## Redeploying after changes

Just re-run the Phase 2 command (e.g. after editing the corpus). Cloud Run builds a new
revision and shifts traffic to it. To add a new secret version later:
```bash
printf 'NEW_KEY' | gcloud secrets versions add LLM_API_KEY --data-file=-
```

## Phase 4 — Custom domain (optional, later)

To serve at `twin.sridharchilukuri.com` instead of the `run.app` URL:
```bash
gcloud beta run domain-mappings create \
  --service digital-twin --region us-central1 \
  --domain twin.sridharchilukuri.com
```
Then add the DNS record it outputs at your registrar. Cloud Run provisions the TLS cert
automatically. One domain can front many apps via subdomains (`twin.`, `app2.`, …).

---

## Notes & gotchas

- **Cold starts:** scale-to-zero means the first request after idle takes a few seconds to
  wake. Fine for a portfolio; if it ever matters, set `--min-instances=1` (leaves the idle
  free tier and costs a few $/mo).
- **Secrets hygiene:** the key lives only in Secret Manager (prod) and `.env` (local). The
  `.dockerignore` keeps `.env` out of the image; `.gitignore` keeps it out of git.
- **Cost:** Cloud Run's free tier (2M requests, ~50 CPU-hours/mo, shared across the account)
  comfortably covers a low-traffic twin → ~$0. LLM tokens are the only real cost.
- **Region:** `us-central1` is a good default; any region works.
