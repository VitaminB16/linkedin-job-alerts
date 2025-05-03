# LinkedIn Job Alerts

This is a mobile push-notification service:

- Deployed as a **Cloud Run**
- Scheduled via **Cloud Scheduler** to run every 10 minutes
- Scrapes LinkedIn job postings via **JobSpy API** library
- Keeps track of the last seen job postings via **Firestore**
- Sends a push notification to a mobile device via **Pushover API** when a new job posting is found
