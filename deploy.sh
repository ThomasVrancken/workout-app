#!/usr/bin/env bash
#
# Build the Docker image via Cloud Build and deploy it to Cloud Run.
# Run this after `terraform apply` has set up the infrastructure.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Reading config from Terraform state..."
cd "$SCRIPT_DIR/infra"
PROJECT_ID=$(terraform output -raw project_id)
REGION=$(terraform output -raw region)
IMAGE=$(terraform output -raw image)
cd "$SCRIPT_DIR"

echo ""
echo "  Project:  $PROJECT_ID"
echo "  Region:   $REGION"
echo "  Image:    $IMAGE"
echo ""

echo "Building image with Cloud Build..."
gcloud builds submit \
  --tag "$IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --quiet

echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy workout-agent \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT_ID"

echo ""
echo "Done! Service URL:"
gcloud run services describe workout-agent \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format "value(status.url)"
