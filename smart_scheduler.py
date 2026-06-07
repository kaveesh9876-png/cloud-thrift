"""
smart_scheduler.py
------------------
Auto-stops and restarts EC2/RDS instances based on environment tags.

Tag your instances:
  Key   : Environment
  Value : dev | staging | qa

Scheduler will:
  - Stop  instances at 8 PM local time on weekdays
  - Stop  instances all day Saturday & Sunday
  - Start instances at 8 AM local time on weekdays
"""

import boto3
from datetime import datetime, timezone
from typing import List


STOP_ENVIRONMENTS  = ["dev", "staging", "qa"]
BUSINESS_HOURS_START = 8   # 8 AM
BUSINESS_HOURS_END   = 20  # 8 PM


def get_tagged_instances(ec2_client, env_values: List[str]) -> List[dict]:
    """Fetch instances tagged with Environment = dev/staging/qa."""
    response = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Environment", "Values": env_values},
            {"Name": "instance-state-name", "Values": ["running", "stopped"]},
        ]
    )
    instances = []
    for reservation in response["Reservations"]:
        for inst in reservation["Instances"]:
            env = next(
                (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Environment"),
                "unknown",
            )
            instances.append({
                "InstanceId": inst["InstanceId"],
                "State":      inst["State"]["Name"],
                "Environment": env,
            })
    return instances


def should_be_running() -> bool:
    """Return True if current time is within business hours on a weekday."""
    now = datetime.now(timezone.utc)
    is_weekday     = now.weekday() < 5   # Mon-Fri
    is_business_hr = BUSINESS_HOURS_START <= now.hour < BUSINESS_HOURS_END
    return is_weekday and is_business_hr


def run_scheduler(region: str = "us-east-1", dry_run: bool = True) -> dict:
    ec2 = boto3.client("ec2", region_name=region)
    instances = get_tagged_instances(ec2, STOP_ENVIRONMENTS)
    running_now = should_be_running()

    to_start = [i["InstanceId"] for i in instances if i["State"] == "stopped" and running_now]
    to_stop  = [i["InstanceId"] for i in instances if i["State"] == "running"  and not running_now]

    print(f"Business hours: {running_now} | Instances scanned: {len(instances)}")
    print(f"  To start: {to_start}")
    print(f"  To stop : {to_stop}")

    if not dry_run:
        if to_start:
            ec2.start_instances(InstanceIds=to_start)
            print(f"Started: {to_start}")
        if to_stop:
            ec2.stop_instances(InstanceIds=to_stop)
            print(f"Stopped: {to_stop}")
    else:
        print("[DRY-RUN] No changes made.")

    return {"started": to_start, "stopped": to_stop}


if __name__ == "__main__":
    run_scheduler(region="us-east-1", dry_run=True)
