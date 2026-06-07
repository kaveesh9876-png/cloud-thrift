"""
handler.py
----------
AWS Lambda entry point for Cloud Thrift nightly cost-audit runs.
Triggered by CloudWatch EventBridge rule (cron: 0 2 * * ? *)  → runs at 2 AM UTC daily.

Environment Variables (set in Lambda console):
  REGION          : AWS region to scan (default: us-east-1)
  DRY_RUN         : "true" / "false"  (default: "true")
  CPU_THRESHOLD   : idle CPU % threshold (default: 5)
  SNS_TOPIC_ARN   : ARN of SNS topic for alert emails (optional)
"""

import json
import os
import boto3

# Add /src to path when running in Lambda layer
import sys
sys.path.insert(0, "/opt/python")

from detectors.ec2_idle_detector import detect_idle_ec2_instances, stop_idle_instances
from detectors.ebs_janitor import find_unattached_volumes, find_old_snapshots, delete_volumes
from detectors.cost_reporter import estimate_savings


def send_sns_alert(topic_arn: str, report: dict) -> None:
    """Publish cost report summary to SNS (email/Slack webhook)."""
    if not topic_arn:
        return
    sns = boto3.client("sns")
    message = (
        f"Cloud Thrift Nightly Audit\n"
        f"{'='*40}\n"
        f"Idle EC2 instances    : {len(report['idle_instances'])}\n"
        f"Unattached volumes    : {len(report['unattached_volumes'])}\n"
        f"Old snapshots (>90d)  : {len(report['old_snapshots'])}\n"
        f"\nEstimated savings/mo  : ${report['savings']['total_monthly_savings']}\n"
        f"Estimated savings/yr  : ${report['savings']['annual_projection']}\n"
        f"\nMode: {'DRY RUN' if report['dry_run'] else 'LIVE — changes applied'}"
    )
    sns.publish(TopicArn=topic_arn, Subject="Cloud Thrift Audit Report", Message=message)


def lambda_handler(event, context):
    """
    Main Lambda handler.
    Called by CloudWatch EventBridge on a nightly schedule.
    """
    region        = os.environ.get("REGION", "us-east-1")
    dry_run       = os.environ.get("DRY_RUN", "true").lower() == "true"
    cpu_threshold = float(os.environ.get("CPU_THRESHOLD", "5"))
    sns_topic     = os.environ.get("SNS_TOPIC_ARN", "")

    print(f"Cloud Thrift audit starting | region={region} | dry_run={dry_run}")

    # 1. Detect idle EC2
    idle_instances = detect_idle_ec2_instances(
        region=region,
        cpu_threshold=cpu_threshold,
        dry_run=dry_run,
    )
    if not dry_run:
        stop_idle_instances(idle_instances, region=region)

    # 2. Detect unattached EBS volumes
    unattached_volumes = find_unattached_volumes(region=region)
    if not dry_run:
        delete_volumes(unattached_volumes, dry_run=False)

    # 3. Detect old snapshots
    old_snapshots = find_old_snapshots(region=region, older_than_days=90)

    # 4. Estimate savings
    savings = estimate_savings(idle_instances, unattached_volumes, old_snapshots)

    report = {
        "idle_instances":     idle_instances,
        "unattached_volumes": unattached_volumes,
        "old_snapshots":      old_snapshots,
        "savings":            savings,
        "dry_run":            dry_run,
        "region":             region,
    }

    # 5. Send SNS alert
    send_sns_alert(sns_topic, report)

    print(f"\nAudit complete. Potential savings: ${savings['total_monthly_savings']}/mo")

    return {
        "statusCode": 200,
        "body": json.dumps(report, default=str),
    }
