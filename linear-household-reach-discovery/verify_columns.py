"""Pull real column schemas from Glue for every candidate table.

Get credentials first (Okta):
    gimme-aws-creds

Then, with a Python that has boto3 (the iceberg-catalog-agent venv does):
    ../iceberg-catalog-agent/.venv/bin/python verify_columns.py
    ../iceberg-catalog-agent/.venv/bin/python verify_columns.py --envs dev

Writes evidence/glue_columns_<date>.json, which build_workbook.py picks up.
"""
import argparse
import json
import os
import re
from datetime import date

import boto3
from botocore.exceptions import BotoCoreError, ClientError

import knowledge as K

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILES = {
    "dev": "aws-adsales-iceberg-dev-WBD_Iceberg_Developer",
    "prod": "aws-adsales-iceberg-prod-WBD_Iceberg_Developer",
}


def columns_of(table):
    sd = table.get("StorageDescriptor", {})
    cols = [[c["Name"], c.get("Type", ""), False] for c in sd.get("Columns", [])]
    cols += [[c["Name"], c.get("Type", ""), True] for c in table.get("PartitionKeys", [])]
    return cols


def collect(env, profile, region):
    glue = boto3.Session(profile_name=profile).client("glue", region_name=region)
    out = {"profile": profile, "tables": {}, "discovery": []}

    for full in K.VERIFY_TABLES:
        db, name = full.split(".", 1)
        try:
            t = glue.get_table(DatabaseName=db, Name=name)["Table"]
            out["tables"][full] = {
                "status": "FOUND",
                "update_time": str(t.get("UpdateTime", "")),
                "table_type": t.get("Parameters", {}).get("table_type", t.get("TableType", "")),
                "columns": columns_of(t),
            }
        except ClientError as e:
            code = e.response["Error"]["Code"]
            out["tables"][full] = {"status": "NOT_FOUND" if code == "EntityNotFoundException" else f"ERROR {code}"}

    rx = re.compile(K.DISCOVERY_PATTERN, re.I)
    for db in K.DISCOVERY_DATABASES:
        try:
            for page in glue.get_paginator("get_tables").paginate(DatabaseName=db):
                for t in page["TableList"]:
                    for col, typ, part in columns_of(t):
                        if rx.search(col):
                            out["discovery"].append([f"{db}.{t['Name']}", col, typ])
        except ClientError as e:
            out["discovery"].append([db, f"ERROR {e.response['Error']['Code']}", ""])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envs", nargs="+", default=["dev", "prod"], choices=sorted(PROFILES))
    ap.add_argument("--region", default="us-east-1")
    args = ap.parse_args()

    result = {"collected": str(date.today()), "envs": {}}
    for env in args.envs:
        try:
            result["envs"][env] = collect(env, PROFILES[env], args.region)
        except (BotoCoreError, ClientError) as e:
            result["envs"][env] = {"error": str(e)}
        r = result["envs"][env]
        if "error" in r:
            print(f"{env}: {r['error']}")
            continue
        found = sum(1 for v in r["tables"].values() if v["status"] == "FOUND")
        print(f"{env}: {found}/{len(r['tables'])} tables found, {len(r['discovery'])} discovery hits")
        for full, exp in K.EXPECTED_COLUMNS.items():
            t = r["tables"].get(full, {})
            if t.get("status") != "FOUND":
                print(f"  {full}: {t.get('status')}")
                continue
            have = {c[0].lower() for c in t["columns"]}
            missing = [c for c in exp if c.lower() not in have]
            print(f"  {full}: {'all expected columns present' if not missing else 'missing ' + ', '.join(missing)}")

    os.makedirs(os.path.join(HERE, "evidence"), exist_ok=True)
    path = os.path.join(HERE, "evidence", f"glue_columns_{date.today()}.json")
    with open(path, "w") as f:
        json.dump(result, f, indent=1)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
