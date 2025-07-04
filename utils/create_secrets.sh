#!/bin/bash

# Load environment variables
source .env

# Check if required variables are set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY not set in .env"
    exit 1
fi

if [ -z "$ATLAS_URI" ]; then
    echo "Error: ATLAS_URI not set in .env"
    exit 1
fi

if [ -z "$GITLAB_TOKEN" ]; then
    echo "Error: GITLAB_TOKEN not set in .env"
    exit 1
fi

# Method 1: Use printf instead of echo -n (most reliable)
printf "%s" "$GOOGLE_API_KEY" | tr -d '\n' | gcloud secrets create google-api-key --data-file=- --project=devpost-ai-in-action
printf "%s" "$ATLAS_URI" | tr -d '\n' | gcloud secrets create atlas-uri --data-file=- --project=devpost-ai-in-action  
printf "%s" "$GITLAB_TOKEN" | tr -d '\n' | gcloud secrets create gitlab-token --data-file=- --project=devpost-ai-in-action

echo "Secrets created successfully!"

# Verify the secrets were created correctly
echo ""
echo "Verifying secrets..."
echo "Google API Key length: $(gcloud secrets versions access latest --secret=google-api-key --project=devpost-ai-in-action | wc -c)"
echo "Atlas URI length: $(gcloud secrets versions access latest --secret=atlas-uri --project=devpost-ai-in-action | wc -c)"
echo "GitLab Token length: $(gcloud secrets versions access latest --secret=gitlab-token --project=devpost-ai-in-action | wc -c)"

# Check if Atlas URI starts correctly
ATLAS_CHECK=$(gcloud secrets versions access latest --secret=atlas-uri --project=devpost-ai-in-action | head -c 10)
echo "Atlas URI starts with: $ATLAS_CHECK"