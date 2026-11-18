"""Check the gutters rig against printed worked examples, then compare with reference/rig_reference.json.

    python reproduce.py

1. HR Wallingford SR620, worked example 2: a 150 mm true half-round eaves gutter, level, drainage length 12.5 m.
   Printed: Q_N 2.38 L/s, design capacity 1.81 L/s. Run with Table 6 and with SR620's equations.
2. AEC Assistant long-eaves-gutter calculator, its own example: rectangular gutter (width = 2 x depth, area 7300 mm2),
   18 m run, fall 1:500, Manning n 0.011, inflow 2.69 L/s. Printed: critical depth at the outlet 37.0 mm, maximum
   depth 56.6 mm. The profile solver must reproduce both, and refining its step must not move them.
3. The two F_L representations agree with each other at every printed row of Table 6 to within 0.007.

Exits nonzero, naming the quantity, if the solver source changed or a number disagrees with the reference.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gutter_capacity as GC        # noqa: E402

AGREE = 1e-9


def sha(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()     # line-ending independent


def compute():
    sec = GC.sr620_half_round_150()
    out = {"worked_example": {"Q_N": GC.q_n(sec["A_E_mm2"]),
                              "table": GC.arm_capacity(12.5, sec, "table"),
                              "equations": GC.arm_capacity(12.5, sec, "equations")}}
    depth = math.sqrt(7300e-6 / 2)
    aec = {}
    for steps in (10000, 40000):
        xs, ys, yc = GC.profile(18.0, 2.69e-3, GC.rect(2 * depth), 1 / 500, 0.011, depth, steps=steps)
        aec[str(steps)] = {"critical_mm": 1e3 * yc, "max_mm": 1e3 * max(ys)}
    out["aec_example"] = aec
    out["table_vs_equations_max_abs"] = max(abs(GC.fl_table(r) - GC.fl_equations(r)) for r in GC.TABLE6_LW)
    return out


def main(write=False):
    ref_path = HERE / "reference" / "rig_reference.json"
    out = compute()
    if write:
        out["source_sha256"] = {"gutter_capacity.py": sha(HERE / "gutter_capacity.py")}
        with open(ref_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1)
            f.write("\n")
        print("reference written")
        return
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    if sha(HERE / "gutter_capacity.py") != ref["source_sha256"]["gutter_capacity.py"]:
        raise SystemExit("source changed: gutter_capacity.py")
    bad = []
    we, rwe = out["worked_example"], ref["worked_example"]
    for k in ("Q_N", "table", "equations"):
        if abs(we[k] - rwe[k]) > AGREE:
            bad.append("worked example %s" % k)
    if round(we["Q_N"], 2) != 2.38 or round(we["equations"], 2) != 1.81 or abs(we["table"] - 1.81) > 0.011:
        bad.append("worked example vs the printed 2.38 / 1.81 L/s")
    for s, v in out["aec_example"].items():
        for k in ("critical_mm", "max_mm"):
            if abs(v[k] - ref["aec_example"][s][k]) > 1e-6:
                bad.append("AEC %s %s" % (s, k))
    a, b = out["aec_example"]["10000"], out["aec_example"]["40000"]
    if round(a["critical_mm"], 1) != 37.0 or round(a["max_mm"], 1) != 56.6:
        bad.append("AEC example vs the printed 37.0 / 56.6 mm")
    if abs(a["max_mm"] - b["max_mm"]) > 1e-3:
        bad.append("AEC example moves with the step")
    if out["table_vs_equations_max_abs"] > 0.007:
        bad.append("Table 6 and the equations disagree")
    if bad:
        raise SystemExit("MISMATCH: " + "; ".join(bad))
    print("SR620 worked example 2 (150 mm half-round, level, 12.5 m): Q_N %.3f L/s (printed 2.38); capacity %.3f L/s "
          "with Table 6, %.3f L/s with the equations (printed 1.81)" % (we["Q_N"], we["table"], we["equations"]))
    print("AEC long-gutter example: critical depth %.1f mm (printed 37.0), maximum depth %.1f mm (printed 56.6); "
          "40,000 steps change it by %.1e mm" % (a["critical_mm"], a["max_mm"], abs(a["max_mm"] - b["max_mm"])))
    print("Table 6 vs the equations, largest difference over the printed rows: %.4f" % out["table_vs_equations_max_abs"])
    print("rig checks match the reference")


if __name__ == "__main__":
    main(write="--write-reference" in sys.argv)
