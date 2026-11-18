"""Same gutter, same parts, move one outlet: how much more rain can the same gutter take?

One straight, level eaves gutter made of N identical 4 m lengths, unions, two stop ends and ONE running outlet.
Only the outlet position changes (it swaps places with a union):
    near the end  - after one length          (arms 4 m and L - 4 m)
    off-centre    - after two lengths         (arms 8 m and L - 8 m)
    centre        - at the middle union       (arms L/2 and L/2)
Section: the idealised SR620 150 mm true half-round (W 75 mm, A_E 8835.73 mm2), not a product profile.
Endpoint: gutter-only design capacity (BS EN 12056-3:2000 5.1.2 / 5.1.6, Table 6 level column per arm; the outlet is
assumed adequate): the largest uniform total inflow both arms carry at their design capacity.

Swept: N = 6, 8, 10 lengths (24, 32, 40 m); F_L from Table 6 and from SR620's equations (separate calculations);
the 5.3.3 strainer reduction (common to all); the outlet reference plane as a common 'lip' h = 0-0.15 m; and, as an
extra stress, independent +-0.15 m shifts of each contender's outlet. A pair is claimed only if its worst ratio
exceeds 1 + max(10 %, 3u), u = the Table 6 two-decimal rounding bound.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import gutter_capacity as GC        # noqa: E402

LENGTH_M = 4.0
COUNTS = (6, 8, 10)
REPS = ("table", "equations")
SHIFT_M = 0.15                       # illustrative stress bound on the outlet position (not a fitting dimension)
LIPS_M = (0.0, 0.05, 0.10, 0.15)
PAIRS = (("off", "end"), ("centre", "off"), ("centre", "end"))
N_RANGE = (0.009, 0.010, 0.011)      # Manning n, PVC with smooth inner walls (Engineering ToolBox, secondary)
NAMES = {"end": "near the end", "off": "off-centre", "centre": "centre"}


def arms(n_lengths):
    total = LENGTH_M * n_lengths
    return {"end": (LENGTH_M, total - LENGTH_M), "off": (2 * LENGTH_M, total - 2 * LENGTH_M),
            "centre": (total / 2, total / 2)}


def capacities(n_lengths, rep, strainer=False, lip=0.0):
    sec = GC.sr620_half_round_150()
    return {k: GC.total_capacity(a, sec, rep, strainer, lip) for k, a in arms(n_lengths).items()}


def corner(n_lengths, rep, strainer=False):
    """(min, max) capacity of each contender with its outlet moved independently by -0.15 / 0 / +0.15 m."""
    sec = GC.sr620_half_round_150()
    out = {}
    for k, (a, b) in arms(n_lengths).items():
        v = [GC.total_capacity((a + e, b - e), sec, rep, strainer) for e in (-SHIFT_M, 0.0, SHIFT_M)]
        out[k] = (min(v), max(v))
    return out


def run():
    sec = GC.sr620_half_round_150()
    res = {"section": sec, "length_m": LENGTH_M}
    nominal, ratios, worst = {}, {}, {f"{a}/{b}": 9.0 for a, b in PAIRS}
    lw_used = []
    for rep in REPS:
        for n in COUNTS:
            c = capacities(n, rep)
            nominal[f"{rep} {n}"] = c
            ratios[f"{rep} {n}"] = {f"{a}/{b}": c[a] / c[b] for a, b in PAIRS}
            for strainer in (False, True):
                cr = corner(n, rep, strainer)
                for a, b in PAIRS:
                    r = cr[a][0] / cr[b][1]
                    worst[f"{a}/{b}"] = min(worst[f"{a}/{b}"], r)
            for a in arms(n).values():
                for e in (-SHIFT_M, 0.0, SHIFT_M):
                    lw_used += [(a[0] + e) * 1000 / sec["W_mm"], (a[1] - e) * 1000 / sec["W_mm"]]
    res["nominal_Ls"], res["nominal_ratios"], res["min_ratio_joint_corner"] = nominal, ratios, worst
    res["strainer_ratios_unchanged"] = all(
        abs(capacities(n, rep, True)[k] / capacities(n, rep)[k] - 0.5) < 1e-12
        for rep in REPS for n in COUNTS for k in ("end", "off", "centre"))
    lip = {}
    for n in COUNTS:
        for h in LIPS_M:
            c = capacities(n, "table", lip=h)
            lip[f"{n} {h:.2f}"] = {f"{a}/{b}": c[a] / c[b] for a, b in PAIRS}
    res["lip_ratios"] = lip
    # numerical bound: Table 6 printed to two decimals -> +-0.005 on F_L, over every F_L used
    f_used = [GC.fl_table(x) for x in lw_used]
    u = 0.005 / min(f_used)
    need = max(0.10, 3 * u)
    res["u"] = {"table_rounding_bound": u, "min_FL_used": min(f_used), "need": need,
                "max_LW": max(lw_used), "min_LW": min(lw_used)}
    res["clears"] = {p: (r - 1 > need) for p, r in worst.items()}
    res["with_opposite_u_penalties"] = {p: r * (1 - u) / (1 + u) for p, r in worst.items()}
    res["no_reversal"] = all(r > 1 for r in worst.values())
    # controls
    res["controls"] = {
        "mirror_after_five_equals_after_one": abs(
            GC.total_capacity((20.0, 4.0), sec) - capacities(6, "table")["end"]) < 1e-12,
        "no_length_factor_ratios": {"off/end": (24 / 16) / (24 / 20), "centre/off": (24 / 12) / (24 / 16),
                                    "centre/end": (24 / 12) / (24 / 20)},
    }
    # the picture: idealised steady profile in each arm at each arrangement's capacity (six lengths, Table 6)
    pic = {}
    r_m = sec["radius_mm"] / 1000.0
    flow = GC.half_round_flow(r_m)
    c6 = capacities(6, "table")
    for k, (a, b) in arms(6).items():
        rows = []
        for arm in (a, b):
            q = c6[k] * arm / (a + b) / 1000.0
            for nn in N_RANGE:
                xs, ys, yc = GC.profile(arm, q, flow, 0.0, nn, r_m)
                rows.append({"arm_m": arm, "n": nn, "critical_mm": 1e3 * yc, "max_mm": 1e3 * max(ys)})
        pic[k] = rows
    res["picture_profiles"] = pic
    gov = [max(r["max_mm"] for r in rows) for rows in pic.values()]
    gov_lo = [max(r["max_mm"] for r in rows if r["n"] == N_RANGE[0]) for rows in pic.values()]
    res["governing_depth_mm"] = {"lo": min(gov_lo), "hi": max(gov), "of_mm": sec["depth_mm"]}
    res["claim"] = {"centre_over_end_at_least": worst["centre/end"],
                    "six_lengths_nominal": ratios["table 6"],
                    "holds": all(res["clears"].values()) and res["no_reversal"]
                    and res["u"]["max_LW"] <= GC.LW_MAX}
    return res
