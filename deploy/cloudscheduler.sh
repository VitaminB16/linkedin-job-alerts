#!/bin/bash

# Cloud scheduler job deployment

# Job: Run the Cloud Function with secret_function option every 10 minutes from 6:00 to 23:50 GMT

# Job configuration
JOB_NAME="linkedin-scheduler-job"
LOCATION="europe-west2"
URI="https://europe-west2-vitaminb16.cloudfunctions.net/linkedin-job-notifier"
SCHEDULE="*/10 8-21 * * *" # Every 10 minutes from 8:00 to 21:50 GMT
TIME_ZONE="Europe/London"
# MESSAGE_BODY_FILE="scheduler_payload.json"
OIDC_SERVICE_ACCOUNT_EMAIL="vitaminb16@vitaminb16.iam.gserviceaccount.com"

configure_job() {
    gcloud scheduler jobs $1 http $JOB_NAME \
        --location $LOCATION \
        --schedule "$SCHEDULE" \
        --time-zone "$TIME_ZONE" \
        --uri "$URI" \
        --http-method POST \
        --oidc-service-account-email $OIDC_SERVICE_ACCOUNT_EMAIL
}

# Check if the job exists and determine action
if gcloud scheduler jobs describe $JOB_NAME --location $LOCATION &>/dev/null; then
    ACTION="update"
else
    ACTION="create"
fi

echo "${ACTION} the job..."
configure_job $ACTION
