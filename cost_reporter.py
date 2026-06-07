"""
cost_reporter.py
----------------
Pulls cost data from AWS Cost Explorer and generates a savings summary report.
Estimates potential monthly savings based on detected waste.
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List


def get_monthly_spend(region: str = "us-east-1") -> Dict:
    """Fetch last 30 days of AWS cost breakdown by service."""
    ce = boto3.client("ce", region_name="us-east-1")  # Cost Explorer is global

    end   = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    results = {}
    for group in response["ResultsByTime"][0]["Groups"]:
        service = group["Keys"][0]
        amount  = float(group["Metrics"]["UnblendedCost"]["Amount"])
        if amount > 0.01:
            results[service] = round(amount, 2)

    return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))


def estimate_savings(
    idle_instances: List[Dict],
    unattached_volumes: List[Dict],
    old_snapshots: List[Dict],
) -> Dict:
    """
    Calculate estimated monthly savings from all detected waste.

    Instance savings = avg hourly cost of instance type * 730 hrs/month
    Volume savings   = size_gb * $0.10/GB/month
    Snapshot savings = size_gb * $0.05/GB/month
    """
    # Rough hourly pricing (on-demand, us-east-1) for common types
    instance_hourly = {
        "t2.micro":   0.0116,
        "t2.small":   0.023,
        "t2.medium":  0.0464,
        "t3.micro":   0.0104,
        "t3.small":   0.0208,
        "t3.medium":  0.0416,
        "t3.large":   0.0832,
        "m5.large":   0.096,
        "m5.xlarge":  0.192,
        "c5.large":   0.085,
        "r5.large":   0.126,
    }
    default_hourly = 0.05  # fallback for unknown types

    ec2_savings  = sum(
        instance_hourly.get(i["InstanceType"], default_hourly) * 730
        for i in idle_instances
    )
    ebs_savings  = sum(v["SizeGB"] * 0.10 for v in unattached_volumes)
    snap_savings = sum(s["SizeGB"] * 0.05 for s in old_snapshots)
    total        = ec2_savings + ebs_savings + snap_savings

    return {
        "ec2_monthly_savings":  round(ec2_savings,  2),
        "ebs_monthly_savings":  round(ebs_savings,  2),
        "snap_monthly_savings": round(snap_savings, 2),
        "total_monthly_savings": round(total,       2),
        "annual_projection":    round(total * 12,   2),
    }


def print_report(spend: Dict, savings: Dict) -> None:
    print("\n" + "=" * 55)
    print("        CLOUD THRIFT — COST AUDIT REPORT")
    print("=" * 55)

    print("\n📊 Top Services by Spend (Last 30 Days):")
    for svc, cost in list(spend.items())[:8]:
        bar = "█" * min(int(cost / 50), 30)
        print(f"  {svc[:35]:<35} ${cost:>8.2f}  {bar}")

    print("\n💰 Estimated Monthly Savings:")
    print(f"  EC2 idle instances  : ${savings['ec2_monthly_savings']:>10.2f}")
    print(f"  Unattached EBS vols : ${savings['ebs_monthly_savings']:>10.2f}")
    print(f"  Old snapshots       : ${savings['snap_monthly_savings']:>10.2f}")
    print(f"  {'─'*35}")
    print(f"  TOTAL / month       : ${savings['total_monthly_savings']:>10.2f}")
    print(f"  TOTAL / year        : ${savings['annual_projection']:>10.2f}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    # In real usage, pass actual results from detectors
    spend = get_monthly_spend()

    # Simulate findings for demo
    demo_idle  = [{"InstanceType": "t3.medium"}, {"InstanceType": "m5.large"}]
    demo_vols  = [{"SizeGB": 100}, {"SizeGB": 50}]
    demo_snaps = [{"SizeGB": 200}, {"SizeGB": 80}]

    savings = estimate_savings(demo_idle, demo_vols, demo_snaps)
    print_report(spend, savings)
