#!/bin/bash

poetry export -f requirements.txt --output requirements.txt --without-hashes

# Convert .env file to .env.yaml by removing GOOGLE_APPLICATION_CREDENTIALS and replacing '=' with ':', adding double quotes around values
awk -F= '{print $1 ": \"" $2 "\""}' .env | grep -v GOOGLE_APPLICATION_CREDENTIALS >yamls/cloudfunction.env.yaml

PROJECT_ID="vitaminb16"
CLOUD_FUNCTION_NAME="linkedin-job-notifier"
REGION="europe-west2"
ENTRY_POINT="main"
RUNTIME="python312"

# Deploy the Cloud Function
gcloud functions deploy $CLOUD_FUNCTION_NAME \
    --project=$PROJECT_ID \
    --runtime=$RUNTIME \
    --trigger-http \
    --entry-point=$ENTRY_POINT \
    --region=$REGION \
    --env-vars-file yamls/cloudfunction.env.yaml \
    --timeout=120s \
    --memory=256MB \
    --no-gen2 \
    --no-allow-unauthenticated
