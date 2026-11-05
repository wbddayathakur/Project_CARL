"""Download the deployed Cube model (staging/core) from S3 into evidence/cube-models-<env>-<date>/.

Only s3:ListBucket and s3:GetObject are called. A _manifest.json records each key's
last-modified time and size; the dashboard reads the deploy date from it.

Run:  .venv-snowflake/bin/python lakehouse-layer-dashboard-v2/pull_cube.py [--envs dev prod]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import boto3

HERE = Path(__file__).resolve().parent
PREFIX = "staging/core/"
BUCKETS = {"dev": "carl-cube-models-us-east-1-dev", "prod": "carl-cube-models-us-east-1-prod"}
SSO_PROFILES = {
    "dev": "aws-adsales-iceberg-dev-WBD_Iceberg_Developer",
    "prod": "aws-adsales-iceberg-prod-WBD_Iceberg_Developer",
}


def pull(env: str, profile: str, out: Path) -> int:
    s3 = boto3.Session(profile_name=profile).client("s3", region_name="us-east-1")
    manifest = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKETS[env], Prefix=PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            dest = out / key[len(PREFIX):]
            dest.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(BUCKETS[env], key, str(dest))
            manifest.append({"key": key, "modified": obj["LastModified"].isoformat(), "size": obj["Size"]})
    (out / "_manifest.json").write_text(json.dumps(manifest, indent=1))
    return len(manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--envs", nargs="+", default=["dev", "prod"])
    parser.add_argument("--profile", action="append", default=[], metavar="ENV=PROFILE",
                        help="Override the AWS profile for one environment")
    args = parser.parse_args()
    profiles = {**SSO_PROFILES, **dict(p.split("=", 1) for p in args.profile)}
    today = dt.date.today().isoformat()
    for env in args.envs:
        out = HERE / "evidence" / f"cube-models-{env}-{today}"
        print(f"{env}: {pull(env, profiles[env], out)} files -> {out}")


if __name__ == "__main__":
    main()
