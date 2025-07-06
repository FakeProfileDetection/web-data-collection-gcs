#!/bin/bash

# Use this if you make changes to index.js, package.json, or .gcloudignore
# This script deploys the Google Cloud Function named "saver".
gcloud functions deploy saver \
  --runtime nodejs20 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-east1 \
  --memory 256MB \
  --timeout 120s \
  --service-account web-data-collection-sa@fake-profile-detection-460117.iam.gserviceaccount.com
