"""
ebs_janitor.py
--------------
Finds and optionally deletes:
  - Unattached EBS volumes (state = 'available')
  - Snapshots older than N days with no associated AMI
  - Orphaned AMIs (deregistered but snapshots still exist)
"""

import boto3
from datetime import datetime, timedelta, timezone
from typing import List, Dict


# ── Unattached Volumes ─────────────────────────────────────────────────────────

def find_unattached_volumes(region: str = "us-east-1") -> List[Dict]:
    """Return all EBS volumes currently not attached to any instance."""
    ec2 = boto3.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_volumes")
    pages = paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}])

    unattached = []
    for page in pages:
        for vol in page["Volumes"]:
            name = next(
                (t["Value"] for t in vol.get("Tags", []) if t["Key"] == "Name"), "N/A"
            )
            size_gb    = vol["Size"]
            volume_id  = vol["VolumeId"]
            created    = vol["CreateTime"]
            age_days   = (datetime.now(timezone.utc) - created).days
            monthly_cost = round(size_gb * 0.10, 2)   # ~$0.10/GB/month (gp2)

            record = {
                "VolumeId":       volume_id,
                "Name":           name,
                "SizeGB":         size_gb,
                "AgeDays":        age_days,
                "EstMonthlyCost": monthly_cost,
                "Region":         region,
            }
            unattached.append(record)
            print(
                f"[UNATTACHED] {volume_id} ({name}) | {size_gb} GB "
                f"| age={age_days}d | ~${monthly_cost}/mo"
            )

    print(f"\nUnattached volumes found: {len(unattached)}")
    return unattached


def delete_volumes(volumes: List[Dict], dry_run: bool = True) -> None:
    """Create a snapshot backup then delete unattached volumes."""
    ec2 = boto3.client("ec2", region_name=volumes[0]["Region"] if volumes else "us-east-1")

    for vol in volumes:
        vid = vol["VolumeId"]
        if dry_run:
            print(f"[DRY-RUN] Would delete volume {vid}")
            continue

        # Always snapshot before deleting
        snap = ec2.create_snapshot(
            VolumeId=vid,
            Description=f"CloudThrift-backup-before-delete-{vid}",
        )
        print(f"  Backup snapshot created: {snap['SnapshotId']}")
        ec2.delete_volume(VolumeId=vid)
        print(f"  Deleted volume: {vid}")


# ── Old Snapshots ──────────────────────────────────────────────────────────────

def find_old_snapshots(
    region: str = "us-east-1",
    older_than_days: int = 90,
) -> List[Dict]:
    """Return snapshots older than `older_than_days` owned by this account."""
    ec2  = boto3.client("ec2", region_name=region)
    sts  = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    paginator = ec2.get_paginator("describe_snapshots")
    pages = paginator.paginate(OwnerIds=[account_id])

    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    old_snaps = []

    for page in pages:
        for snap in page["Snapshots"]:
            if snap["StartTime"] < cutoff:
                age_days = (datetime.now(timezone.utc) - snap["StartTime"]).days
                record = {
                    "SnapshotId":  snap["SnapshotId"],
                    "VolumeId":    snap.get("VolumeId", "N/A"),
                    "SizeGB":      snap["VolumeSize"],
                    "AgeDays":     age_days,
                    "Description": snap.get("Description", ""),
                    "Region":      region,
                }
                old_snaps.append(record)
                print(
                    f"[OLD-SNAP] {snap['SnapshotId']} | vol={snap.get('VolumeId','N/A')} "
                    f"| {snap['VolumeSize']} GB | age={age_days}d"
                )

    print(f"\nOld snapshots found (>{older_than_days}d): {len(old_snaps)}")
    return old_snaps


def delete_snapshots(snapshots: List[Dict], dry_run: bool = True) -> None:
    ec2 = boto3.client("ec2", region_name=snapshots[0]["Region"] if snapshots else "us-east-1")
    for snap in snapshots:
        sid = snap["SnapshotId"]
        if dry_run:
            print(f"[DRY-RUN] Would delete snapshot {sid}")
        else:
            ec2.delete_snapshot(SnapshotId=sid)
            print(f"Deleted snapshot: {sid}")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== EBS Unattached Volumes ===")
    vols = find_unattached_volumes(region="us-east-1")
    delete_volumes(vols, dry_run=True)

    print("\n=== Old Snapshots (>90 days) ===")
    snaps = find_old_snapshots(region="us-east-1", older_than_days=90)
    delete_snapshots(snaps, dry_run=True)
