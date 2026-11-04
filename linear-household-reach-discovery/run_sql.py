"""Render the validation SQL pack and optionally run it on Athena.

    python3 run_sql.py --render-only                     # writes sql/rendered/*.sql for the Athena console
    ../iceberg-catalog-agent/.venv/bin/python run_sql.py --workgroup primary 01 04
    ../iceberg-catalog-agent/.venv/bin/python run_sql.py --workgroup primary --output s3://bucket/prefix/

Each numbered file is prefixed with sql/_base.sql unless its header says "Standalone".
Results go to out/sql_results/<file>.csv.
"""
import argparse
import csv
import glob
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SQL = os.path.join(HERE, "sql")
PROFILES = {
    "dev": "aws-adsales-iceberg-dev-WBD_Iceberg_Developer",
    "prod": "aws-adsales-iceberg-prod-WBD_Iceberg_Developer",
}


def render(path):
    body = open(path).read()
    if "Standalone" in body.split("\n", 1)[0]:
        return body
    return open(os.path.join(SQL, "_base.sql")).read().rstrip() + "\n" + body


def run_athena(client, sql, workgroup, output):
    kw = {"QueryString": sql, "WorkGroup": workgroup}
    if output:
        kw["ResultConfiguration"] = {"OutputLocation": output}
    qid = client.start_query_execution(**kw)["QueryExecutionId"]
    while True:
        st = client.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if st["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(2)
    if st["State"] != "SUCCEEDED":
        return st["State"], st.get("StateChangeReason", ""), []
    rows = []
    for page in client.get_paginator("get_query_results").paginate(QueryExecutionId=qid):
        for r in page["ResultSet"]["Rows"]:
            rows.append([c.get("VarCharValue", "") for c in r["Data"]])
    return "SUCCEEDED", "", rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="file number prefixes to run, e.g. 01 04")
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--env", default="dev", choices=sorted(PROFILES))
    ap.add_argument("--workgroup", default="primary")
    ap.add_argument("--output", help="S3 output location if the workgroup does not enforce one")
    ap.add_argument("--region", default="us-east-1")
    args = ap.parse_args()

    files = sorted(f for f in glob.glob(os.path.join(SQL, "[0-9][0-9]_*.sql"))
                   if not args.only or os.path.basename(f)[:2] in args.only)
    os.makedirs(os.path.join(SQL, "rendered"), exist_ok=True)
    rendered = {}
    for f in files:
        rendered[f] = render(f)
        with open(os.path.join(SQL, "rendered", os.path.basename(f)), "w") as out:
            out.write(rendered[f])
    print(f"rendered {len(files)} files into sql/rendered/")
    if args.render_only:
        return

    import boto3
    client = boto3.Session(profile_name=PROFILES[args.env]).client("athena", region_name=args.region)
    res_dir = os.path.join(HERE, "out", "sql_results")
    os.makedirs(res_dir, exist_ok=True)
    for f, sql in rendered.items():
        name = os.path.basename(f)
        state, reason, rows = run_athena(client, sql, args.workgroup, args.output)
        if state == "SUCCEEDED":
            with open(os.path.join(res_dir, name.replace(".sql", ".csv")), "w", newline="") as out:
                csv.writer(out).writerows(rows)
            print(f"{name}: {max(len(rows) - 1, 0)} rows")
        else:
            print(f"{name}: {state} {reason}")


if __name__ == "__main__":
    main()
