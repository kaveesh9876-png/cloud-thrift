"""
ec2_idle_detector.py
--------------------
Detects EC2 instances with average CPU utilization < 5% over the last 14 days.
Uses CloudWatch metrics to identify idle/underutilized instances.
"""

import boto3
from datetime import datetime, timedelta, timezone
from typing import List, Dict


def get_cloudwatch_cpu_average(cw_client, instance_id: str, days: int = 14) -> float:
    """Return average CPU utilization (%) for a given instance over last N days."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)

    response = cw_client.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=86400,          # 1-day granularity
        Statistics=["Average"],
    )

    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return 0.0

    return sum(d["Average"] for d in datapoints) / len(datapoints)


def detect_idle_ec2_instances(
    region: str = "us-east-1",
    cpu_threshold: float = 5.0,
    lookback_days: int = 14,
    dry_run: bool = True,
) -> List[Dict]:
    """
    Scan all running EC2 instances and return those below the CPU threshold.

    Parameters
    ----------
    region        : AWS region to scan
    cpu_threshold : Instances with avg CPU below this % are flagged (default 5%)
    lookback_days : How many days of CloudWatch history to analyse
    dry_run       : If True, only report — never stop/terminate anything

    Returns
    -------
    List of dicts with idle instance details
    """
    ec2 = boto3.client("ec2", region_name=region)
    cw  = boto3.client("cloudwatch", region_name=region)

    # Fetch all running instances
    paginator = ec2.get_paginator("describe_instances")
    pages = paginator.paginate(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])

    idle_instances = []

    for page in pages:
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                instance_id   = instance["InstanceId"]
                instance_type = instance["InstanceType"]
                launch_time   = instance["LaunchTime"]

                # Skip instances launched less than lookback_days ago
                age_days = (datetime.now(timezone.utc) - launch_time).days
                if age_days < lookback_days:
                    continue

                avg_cpu = get_cloudwatch_cpu_average(cw, instance_id, lookback_days)

                # Get Name tag if present
                name = next(
                    (t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"),
                    "N/A",
                )

                if avg_cpu < cpu_threshold:
                    record = {
                        "InstanceId":   instance_id,
                        "Name":         name,
                        "InstanceType": instance_type,
                        "AvgCPU":       round(avg_cpu, 2),
                        "AgeDays":      age_days,
                        "Region":       region,
                        "DryRun":       dry_run,
                    }
                    idle_instances.append(record)
                    print(
                        f"[IDLE] {instance_id} ({name}) | type={instance_type} "
                        f"| avg_cpu={avg_cpu:.2f}% | age={age_days}d"
                    )

    print(f"\nTotal idle instances found: {len(idle_instances)}")
    return idle_instances


def stop_idle_instances(idle_instances: List[Dict], region: str = "us-east-1") -> None:
    """Stop a list of idle instances (only called when dry_run=False)."""
    ec2 = boto3.client("ec2", region_name=region)
    ids = [i["InstanceId"] for i in idle_instances if not i["DryRun"]]

    if not ids:
        print("Dry-run mode — no instances stopped.")
        return

    ec2.stop_instances(InstanceIds=ids)
    print(f"Stopped {len(ids)} idle instance(s): {ids}")


if __name__ == "__main__":
    idle = detect_idle_ec2_instances(region="us-east-1", dry_run=True)
    # To actually stop them: set dry_run=False and call stop_idle_instances(idle)
