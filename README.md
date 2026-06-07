# ⚡ Cloud Thrift — AWS Cost Optimization Bot

> Automated detection and elimination of AWS cloud waste using Boto3 + Lambda + CloudWatch.  
> Reduces simulated monthly cloud spend by **~30%** with zero manual effort.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?style=flat-square&logo=amazon-aws)
![Boto3](https://img.shields.io/badge/Boto3-1.34-yellow?style=flat-square)
![CloudWatch](https://img.shields.io/badge/CloudWatch-Triggers-red?style=flat-square&logo=amazon-aws)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📌 What It Does

Cloud Thrift is a **serverless cost-audit bot** deployed on AWS Lambda.  
Every night at 2 AM UTC, it automatically:

| Module | What It Detects | Savings |
|---|---|---|
| **EC2 Idle Detector** | Instances with avg CPU < 5% over 14 days | Stop = 100% of instance cost |
| **EBS Janitor** | Unattached volumes + snapshots older than 90 days | ~$0.10/GB/month per volume |
| **Smart Scheduler** | Dev/staging instances running nights & weekends | Up to 65% on non-prod |
| **Cost Reporter** | Full spend breakdown via Cost Explorer API | Identifies top waste areas |

**Result:** ~30% reduction in simulated monthly AWS spend across test environments.

---

## 🏗️ Architecture

```
AWS Accounts
    │
    ▼
CloudWatch EventBridge  ──(cron: 0 2 * * ? *)──▶  Lambda (handler.py)
                                                        │
                          ┌─────────────────────────────┤
                          │                             │
                          ▼                             ▼
                   EC2 / EBS / Snapshots          Cost Explorer API
                   (Boto3 describe/stop)          (monthly spend data)
                          │
                          ▼
                   SNS Topic ──▶ Email / Slack Alert
```

- **No servers to manage** — runs entirely on Lambda (512 MB, 5 min timeout)
- **Read-only by default** — `DRY_RUN=true` env var, no changes without opt-in
- **Least-privilege IAM** — exact permissions listed in `lambda/eventbridge_rule.json`
- **Always backs up** before deleting any EBS volume (snapshot created first)

---

## 📁 Project Structure

```
cloud-thrift/
├── lambda/
│   ├── handler.py               # Lambda entry point
│   └── eventbridge_rule.json    # CloudWatch trigger config + IAM policy
├── src/
│   ├── detectors/
│   │   ├── ec2_idle_detector.py # CPU-based idle instance scanner
│   │   ├── ebs_janitor.py       # Unattached volumes + old snapshot cleaner
│   │   └── cost_reporter.py     # Cost Explorer + savings estimator
│   └── scheduler/
│       └── smart_scheduler.py   # Env-tag-based start/stop scheduler
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Deployment

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/cloud-thrift.git
cd cloud-thrift
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

```bash
aws configure
# or use environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Run Locally (Dry Run)

```bash
# Detect idle EC2 instances
python src/detectors/ec2_idle_detector.py

# Find unattached EBS volumes + old snapshots
python src/detectors/ebs_janitor.py

# Generate cost report
python src/detectors/cost_reporter.py

# Run smart scheduler
python src/scheduler/smart_scheduler.py
```

### 4. Deploy to Lambda

```bash
# Package for Lambda
zip -r cloud-thrift.zip lambda/ src/ requirements.txt

# Create Lambda function (AWS CLI)
aws lambda create-function \
  --function-name cloud-thrift-audit \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/cloud-thrift-role \
  --handler lambda/handler.lambda_handler \
  --zip-file fileb://cloud-thrift.zip \
  --timeout 300 \
  --environment Variables="{REGION=us-east-1,DRY_RUN=true,CPU_THRESHOLD=5}"

# Create nightly CloudWatch trigger
aws events put-rule \
  --name cloud-thrift-nightly \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `REGION` | `us-east-1` | AWS region to scan |
| `DRY_RUN` | `true` | `false` to apply changes |
| `CPU_THRESHOLD` | `5` | % CPU below which instance is flagged |
| `SNS_TOPIC_ARN` | `` | SNS ARN for email/Slack alerts |

---

## 📊 Sample Output

```
[IDLE] i-0abc123 (my-dev-server) | type=t3.medium | avg_cpu=1.24% | age=42d
[IDLE] i-0def456 (staging-api)   | type=m5.large  | avg_cpu=2.87% | age=28d

Total idle instances found: 2

[UNATTACHED] vol-0xyz789 (old-backup) | 100 GB | age=67d | ~$10.00/mo
[UNATTACHED] vol-0abc111 (N/A)        |  50 GB | age=12d | ~$5.00/mo

Unattached volumes found: 2

===================================================
        CLOUD THRIFT — COST AUDIT REPORT
===================================================

💰 Estimated Monthly Savings:
  EC2 idle instances  :     $121.68
  Unattached EBS vols :      $15.00
  Old snapshots       :      $14.00
  ─────────────────────────────────
  TOTAL / month       :     $150.68
  TOTAL / year        :   $1,808.16
===================================================
```

---

## 🔒 Security

- **Read-only IAM by default** — `ReadOnlyAccess` policy for analysis mode
- **No credentials stored** — uses IAM roles for Lambda execution
- **Backup before delete** — every volume deletion creates a snapshot first
- **Audit trail** — all actions logged to CloudWatch Logs

---

## 🛠️ Tech Stack

- **Python 3.11** — core language
- **AWS Boto3** — EC2, EBS, CloudWatch, Cost Explorer, SNS APIs
- **AWS Lambda** — serverless execution (no servers to manage)
- **CloudWatch EventBridge** — nightly cron scheduling
- **SNS** — email/Slack alert delivery

---

## 📄 License

MIT — free to use, modify, and distribute.
