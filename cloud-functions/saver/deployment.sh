#!/bin/bash
gcloud functions deploy saver \
  --runtime nodejs20 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-east1 \
  --memory 256MB \
  --timeout 120s \
  --service-account web-data-collection-sa@fake-profile-detection-460117.iam.gserviceaccount.com
