"""Reproduce "Move one outlet: how much more rain can the same gutter take?" from frozen sources.

    python reproduce.py            (from this folder; needs the rig's gutter_capacity.py one level up)
    python reproduce.py --freeze   (maintainers only: rewrite reference/result.json from this run)

Re-runs the gutter-only design capacity of the three outlet positions for 6, 8 and 10 lengths with Table 6 and with
SR620's equations, the strainer branch, the outlet reference-plane sweep, the +-0.15 m stress corners, the numerical
bound, the controls and the idealised water profiles drawn in the video; compares every number with
reference/result.json. Exits nonzero, naming the quantity, if a source changed or a number disagrees.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "solver"))
REF = HERE / "reference" / "result.json"
SOURCES = ("solver/outlet_study.py", "../gutter_capacity.py")
REL = 1e-9


def sha(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()     # line-ending independent


def flat(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flat(v, "%s/%s" % (prefix, k) if prefix else str(k)))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            out.update(flat(v, "%s[%d]" % (prefix, i)))
    else:
        out[prefix] = obj
    return out


def same(a, b):
    if isinstance(a, (bool, str)) or isinstance(b, (bool, str)) or a is None or b is None:
        return a == b
    return abs(float(a) - float(b)) <= REL * max(1.0, abs(float(b)))


def main():
    import outlet_study as S
    freeze = "--freeze" in sys.argv
    if not freeze:
        ref = json.loads(REF.read_text(encoding="utf-8"))
        for rel, want in ref["source_sha256"].items():
            if sha((HERE / rel).resolve()) != want:
                raise SystemExit("source changed: %s" % rel)
    res = json.loads(json.dumps(S.run()))
    if freeze:
        res["source_sha256"] = {rel: sha((HERE / rel).resolve()) for rel in SOURCES}
        REF.parent.mkdir(exist_ok=True)
        with open(REF, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=1, sort_keys=True)
            f.write("\n")
        print("frozen ->", REF)
        return
    got, want = flat(res), flat({k: v for k, v in ref.items() if k != "source_sha256"})
    bad = sorted(k for k in set(got) | set(want) if k not in got or k not in want or not same(got[k], want[k]))
    if bad:
        raise SystemExit("MISMATCH: " + "; ".join(bad[:20]))
    if not res["claim"]["holds"]:
        raise SystemExit("the registered claim does not hold")

    print("Gutter-only design capacity (outlet assumed adequate), idealised 150 mm half-round, level, L/s:")
    print("  lengths | representation | near the end | off-centre | centre | centre / near the end")
    for key, c in res["nominal_Ls"].items():
        rep, n = key.split()
        print("  %7s | %-14s | %12.3f | %10.3f | %6.3f | x%.3f"
              % (n, rep, c["end"], c["off"], c["centre"], res["nominal_ratios"][key]["centre/end"]))
    w = res["min_ratio_joint_corner"]
    u = res["u"]
    print("\nWorst case over 6/8/10 lengths, both representations, strainer, +-0.15 m outlet shifts:")
    print("  off-centre / near the end x%.3f, centre / off-centre x%.3f, centre / near the end x%.3f"
          % (w["off/end"], w["centre/off"], w["centre/end"]))
    print("  Table 6 rounding bound u %.2f %% -> need max(10 %%, 3u) = %.0f %%; every pair clears: %s"
          % (100 * u["table_rounding_bound"], 100 * u["need"], all(res["clears"].values())))
    print("  L/W used %.0f-%.0f (Table 6 stops at 500; nothing extrapolated)" % (u["min_LW"], u["max_LW"]))
    g = res["governing_depth_mm"]
    print("Idealised water profile at capacity (n 0.009-0.011): deepest point %.1f-%.1f mm of the %.0f mm depth"
          % (g["lo"], g["hi"], g["of_mm"]))
    print("all checks pass; every number matches the frozen reference")


if __name__ == "__main__":
    main()
