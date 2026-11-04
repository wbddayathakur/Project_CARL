import csv
import re
from collections import Counter
from pathlib import Path

BASE = Path("/tmp/mr/tax")
SAMPLES = Path("/Users/dthakur/Downloads/MarketResearch-sample")


def load(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    return [h.strip() for h in rows[0]], rows[1:]


SCI = re.compile(r"^-?\d+(\.\d+)?E[+-]\d+$", re.I)
MANGLED_TS = re.compile(r"^\d{1,2}:\d{2}(\.\d)?$")
LEADING_ZERO = re.compile(r"^0\d+$")


def profile(label, path, keys=()):
    hdr, rows = load(path)
    print(f"\n### {label}  ({path.name})  rows={len(rows)} cols={len(hdr)}")
    print("header:", hdr)
    blank = sum(1 for r in rows if not any(c.strip() for c in r))
    print("fully blank rows:", blank)
    for i, h in enumerate(hdr):
        vals = [r[i] if i < len(r) else "" for r in rows]
        nn = [v for v in vals if v.strip()]
        sci = sum(1 for v in nn if SCI.match(v.strip()))
        ts = sum(1 for v in nn if MANGLED_TS.match(v.strip()))
        lz = sum(1 for v in nn if LEADING_ZERO.match(v.strip()))
        pad = sum(1 for v in nn if v != v.strip())
        distinct = len(set(nn))
        flags = []
        if sci: flags.append(f"sci-notation={sci}")
        if ts: flags.append(f"mangled-ts={ts}")
        if lz: flags.append(f"leading-zero={lz}")
        if pad: flags.append(f"padded={pad}")
        top = Counter(nn).most_common(4) if distinct <= 40 else ""
        print(f"  {h:34s} non-null={len(nn):5d} distinct={distinct:5d} {' '.join(flags)} {top}")
    for k in keys:
        idx = [hdr.index(c) for c in k]
        c = Counter(tuple(r[i].strip() for i in idx) for r in rows if any(r))
        d = {kk: v for kk, v in c.items() if v > 1}
        print(f"  key {k}: duplicates={len(d)} {list(d.items())[:3]}")
    return hdr, rows


def diff(name, key):
    hi, ri = load(BASE / "input" / name)
    ho, ro = load(BASE / "output" / name)
    hi_u = [h.upper().replace(" ", "") for h in hi]
    ho_u = [h.upper().replace(" ", "") for h in ho]
    ki = [hi_u.index(k) for k in key]
    ko = [ho_u.index(k) for k in key]
    si = {tuple(r[i].strip() for i in ki) for r in ri if any(c.strip() for c in r)}
    so = {tuple(r[i].strip() for i in ko) for r in ro if any(c.strip() for c in r)}
    print(f"\n### input vs output {name} on {key}: input={len(si)} output={len(so)} "
          f"only_in_input={len(si - so)} only_in_output={len(so - si)}")
    print("  only_in_output sample:", sorted(so - si)[:6])
    print("  only_in_input sample:", sorted(si - so)[:6])
    print("  header diff:", set(hi_u) ^ set(ho_u))


print("=" * 20, "TAXONOMY INPUT (what Research edits)")
profile("distributormapping", BASE / "input/distributormapping.csv", keys=[("DISTRIBUTORCODE",)])
profile("network", BASE / "input/network.csv", keys=[("_NETWORKSK",), ("NAME",)])
profile("fourpartgenre", BASE / "input/fourpartgenre.csv", keys=[("ProgramTypeCd", "ProgramSubTypeCd")])
profile("productcategories", BASE / "input/productcategories.csv", keys=[("ID",), ("ADINTELPRODUCTID",)])
profile("rules_engine", BASE / "input/rules_engine.csv", keys=[("Priority", "Name", "ProgramTypeDescription", "Program")])

print("\n" + "=" * 20, "TAXONOMY OUTPUT (what the ETL writes back)")
profile("distributormapping out", BASE / "output/distributormapping.csv")
profile("network out", BASE / "output/network.csv")
profile("fourpartgenre out", BASE / "output/fourpartgenre.csv", keys=[("PROGRAMTYPECD", "PROGRAMSUBTYPECD")])

diff("distributormapping.csv", ["DISTRIBUTORCODE"])
diff("network.csv", ["_NETWORKSK"])
diff("fourpartgenre.csv", ["PROGRAMTYPECD", "PROGRAMSUBTYPECD"])
diff("productcategories.csv", ["ID"])

print("\n" + "=" * 20, "SNOWFLAKE SAMPLES")
profile("dimNetwork", SAMPLES / "dimNetwork2026-10-23.csv")
profile("dimAdvertiserBrand", SAMPLES / "dimAdvertiserBrand-Limit100-2026-10-23.csv")
profile("dimNetworkProgramNameMapping", SAMPLES / "dimNetworkProgramNameMapping-Limit100-2026-10-23.csv")
