"""Rebuild every deliverable in out/. Usage: python3 build.py   (needs Python 3 + openpyxl only)."""
import os
import analysis, build_master, build_custom, build_lineage, build_profiles, build_docs
from common import OUT

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    A = analysis.run()
    built = {"master": build_master.build(A), "custom": build_custom.build(A)}
    built["sflin"] = build_lineage.build_sf(A)[0]
    built["op1lin"] = build_lineage.build_op1(A)
    built["prof"] = build_profiles.build(A)
    docs = build_docs.build(A, built)
    for v in list(built.values()) + docs:
        print(v)
