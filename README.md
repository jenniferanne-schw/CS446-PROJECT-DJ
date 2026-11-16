# CS446-PROJECT
CS446 427B Cloud Computing Project: Smart Price Drop Tracker on AWS

Smart Price Drop Tracker on AWS

An automated, serverless price-monitoring and alert system built entirely on AWS using non-networking services. This application periodically tracks asset prices (such as cryptocurrencies) against user-defined targets, logs historical audit trails, triggers automated email notifications, and provides an interactive web dashboard.

---

Architecture & AWS Services Used
This project strictly utilizes 4 core AWS services (avoiding any networking/purple services) to maintain a zero-cost architecture:

1. **AWS Lambda (Python 3.13):** Computes backend logic, queries the CoinGecko API, evaluates target prices, and manages data read/writes.
2. **Amazon DynamoDB (`PriceMatchList`):** Serves as the serverless NoSQL database storing watchlist items, API endpoints, target prices, and latest market states.
3. **Amazon S3:** Used across two buckets:
   - **Static Website Hosting Bucket (`price-tracker-web-2111-dj`):** Hosts the frontend web dashboard.
   - **Private Audit Logs Bucket (`price-drop-logs-2111-dj`):** Persists timestamped JSON reports (`deals_...json`) whenever a price drop target is met.
4. **Amazon CloudWatch:** Automates scheduling (via EventBridge rules), ingests execution logs, runs **Metric Filters** (`PRICE_DROP_FOUND`), and drives **CloudWatch Alarms** tied to Amazon SNS for instant email alerts.

---

Data Flow
1. **Schedule Trigger:** CloudWatch invokes the Lambda function on a regular schedule (e.g., every 1 hour).
2. **Database Scan:** Lambda scans DynamoDB to retrieve tracked assets.
3. **API Poll & Evaluation:** Lambda queries the CoinGecko JSON API, updates `last_price` in DynamoDB, and checks if current prices meet or drop below targets.
4. **Audit Logging:** If a price drop is detected, a timestamped report is saved to the private S3 audit bucket, and a custom keyword (`PRICE_DROP_FOUND`) is logged.
5. **Automated Alert:** CloudWatch detects the keyword via a Metric Filter, transitions the alarm state, and dispatches an email notification via SNS.
6. **Frontend Interaction:** Users can visit the S3 static web dashboard to view live prices, add new assets to DynamoDB, or trigger on-demand price checks via secure Lambda Function URLs.

---

Step-by-Step Deployment Guide
For complete step-by-step reproduction instructions, console screenshots, and IAM role configurations, please refer to our full project documentation:
**[View Full Project Manual (Google Docs / PDF)](https://docs.google.com/document/d/1nvRsn-9ePnDScrWdK0563G_Y1T7CPdYs/edit?usp=sharing&ouid=102893575658134746164&rtpof=true&sd=true)**
