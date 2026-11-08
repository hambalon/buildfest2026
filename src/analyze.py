"""Summary statistics for the cleaned survey.

Usage (from the repo root):
    python -m src.analyze            # writes CSV tables to outputs/

Outputs (all gitignored):
    outputs/overall.csv          headline numbers
    outputs/retro_change.csv     before (retrospective) vs after, per item
    outputs/by_county.csv        metrics by county   (with n and suppression flag)
    outputs/by_role.csv          metrics by role     (multi-select roles counted in each)
    outputs/by_language.csv      metrics by language

Small-group rule: any group with n < MIN_N (src/config.py, default 10) has its
metrics blanked and `suppressed = True`. Report those groups as "n<10" only.
"""
from __future__ import annotations

import pandas as pd

from src import config as C
from src.clean import CleanResult, group_small, load_and_clean, save_outputs

try:
    from scipy.stats import kruskal, mannwhitneyu, wilcoxon
except ImportError:  # scipy is optional; p-values are skipped without it
    kruskal = mannwhitneyu = wilcoxon = None


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #
def top_box(s: pd.Series) -> float:
    s = s.dropna().astype(float)
    return float((s >= C.TOP_BOX_MIN).mean() * 100) if len(s) else float("nan")


def pct_likely_988(res: CleanResult, s: pd.Series) -> float:
    """% likely to call 988: 4-5 on a 1-5 label scale, or >= CALL_988_LIKELY_MIN_0_10 on 0-10."""
    if res.call_988_scale == "0-10":
        s = s.dropna().astype(float)
        return float((s >= C.CALL_988_LIKELY_MIN_0_10).mean() * 100) if len(s) else float("nan")
    return top_box(s)


def nps(s: pd.Series) -> float:
    """Net Promoter Score: % 9-10 minus % 0-6."""
    s = s.dropna().astype(float)
    if not len(s):
        return float("nan")
    return float(((s >= 9).mean() - (s <= 6).mean()) * 100)


def person_retro_change(res: CleanResult, df: pd.DataFrame) -> pd.Series:
    """Each respondent's average (after - before) across all paired items."""
    diffs = [df[l].astype(float) - df[r].astype(float)
             for r, l in res.retro_pairs.items() if l]
    if not diffs:
        return pd.Series(float("nan"), index=df.index)
    return pd.concat(diffs, axis=1).mean(axis=1)


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
def overall(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Headline numbers. A metric answered by fewer than MIN_N people is blanked
    (its "n answered" row stays, so callers can show "n<10")."""
    df = res.df if df is None else df
    rows = [("Responses", len(df))]

    def block(n_name, n, metrics):
        ok = n >= C.MIN_N
        return [(n_name, n)] + [(name, fn() if ok else float("nan")) for name, fn in metrics]

    if "recommend" in df:
        s = df["recommend"]
        rows += block("Recommend: n answered", int(s.notna().sum()), [
            ("Recommend: mean (0-10)", lambda: round(s.astype(float).mean(), 2)),
            ("Net Promoter Score", lambda: round(nps(s), 1))])
    if "call_988" in df:
        s = df["call_988"]
        metrics = [("Likely to call 988: % likely", lambda: round(pct_likely_988(res, s), 1))]
        if res.call_988_scale == "0-10":
            metrics += [("Likely to call 988: mean (0-10)", lambda: round(s.astype(float).mean(), 2))]
        rows += block("Likely to call 988: n answered", int(s.notna().sum()), metrics)
    if res.retro_pairs:
        ch = person_retro_change(res, df)
        rows += block("Retro change: n with any pair", int(ch.notna().sum()), [
            ("Retro change: mean points (1-5 scale)", lambda: round(ch.mean(), 2)),
            ("Retro change: % who improved on average",
             lambda: round((ch.dropna() > 0).mean() * 100, 1))])
    return pd.DataFrame(rows, columns=["metric", "value"])


def retro_change(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Before (retrospective) vs after for each paired item. Uses only people who
    answered both halves of the pair."""
    df = res.df if df is None else df
    rows = []
    for rcol, lcol in res.retro_pairs.items():
        if not lcol:
            continue
        pair = df[[rcol, lcol]].dropna().astype(float)
        n = len(pair)
        d = pair[lcol] - pair[rcol]
        row = {
            "item": lcol,
            "question_after": res.label(lcol),
            "question_before": res.label(rcol),
            "n": n,
            "suppressed": n < C.MIN_N,
            "before_mean": pair[rcol].mean(),
            "after_mean": pair[lcol].mean(),
            "change": d.mean(),
            "pct_improved": (d > 0).mean() * 100 if n else float("nan"),
            "pct_same": (d == 0).mean() * 100 if n else float("nan"),
            "pct_declined": (d < 0).mean() * 100 if n else float("nan"),
            "top_box_before": top_box(pair[rcol]),
            "top_box_after": top_box(pair[lcol]),
            "wilcoxon_p": float("nan"),
        }
        if wilcoxon is not None and n >= C.MIN_N and (d != 0).any():
            row["wilcoxon_p"] = float(wilcoxon(d[d != 0]).pvalue)
        if row["suppressed"]:
            for k in row:
                if k not in ("item", "question_after", "question_before", "n", "suppressed"):
                    row[k] = float("nan")
        rows.append(row)
    out = pd.DataFrame(rows)
    num = out.columns.difference(["item", "question_after", "question_before", "n", "suppressed", "wilcoxon_p"])
    out[num] = out[num].round(3)
    return out  # wilcoxon_p left unrounded: tiny values would show as 0


def _metrics(res: CleanResult, g: pd.DataFrame) -> dict:
    """Metrics for one group. Each metric is blanked if fewer than MIN_N people in
    the group answered that question (its n_* column says how many did)."""
    m = {}

    def put(name, n, value):
        m[name] = value if n >= C.MIN_N else float("nan")

    if "recommend" in g:
        n = int(g["recommend"].notna().sum())
        m["n_recommend"] = n
        put("recommend_mean", n, g["recommend"].astype(float).mean())
        put("nps", n, nps(g["recommend"]))
    if "call_988" in g:
        n = int(g["call_988"].notna().sum())
        m["n_988"] = n
        put("pct_likely_988", n, pct_likely_988(res, g["call_988"]))
    if res.retro_pairs:
        ch = person_retro_change(res, g)
        n = int(ch.notna().sum())
        m["n_retro"] = n
        put("retro_change_mean", n, ch.mean())
    for col in res.likert_cols:
        n = int(g[col].notna().sum())
        m[f"n_agree_{col}"] = n
        put(f"pct_agree_{col}", n, top_box(g[col]))
    return m


def by_group(res: CleanResult, group: str, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Metrics per group with n and suppression. group: 'county', 'language' or 'role'."""
    df = res.df if df is None else df
    if group == "role":
        if "role_list" not in df:
            return pd.DataFrame()
        ex = df.explode("role_list")
        ex["group"] = group_small(ex["role_list"].replace("", pd.NA))
        ex = ex.reset_index().drop_duplicates(["index", "group"]).set_index("index")
    else:
        col = f"{group}_grp"
        if col not in df:
            return pd.DataFrame()
        ex = df.assign(group=df[col])

    rows = []
    for name, g in ex.groupby("group", observed=True):
        row = {"group": name, "n": len(g), "suppressed": len(g) < C.MIN_N}
        metrics = _metrics(res, g)
        if row["suppressed"]:  # hide everything, including the per-metric n's
            metrics = {k: float("nan") for k in metrics}
        rows.append({**row, **metrics})
    out = pd.DataFrame(rows).sort_values("n", ascending=False)
    return out.round(2).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Robustness checks (stage 03)
# --------------------------------------------------------------------------- #
def _p(test, a: pd.Series, b: pd.Series) -> float:
    a, b = a.dropna().astype(float), b.dropna().astype(float)
    if test is None or len(a) < C.MIN_N or len(b) < C.MIN_N:
        return float("nan")
    try:
        return float(test(a, b).pvalue)
    except ValueError:  # e.g. all values identical
        return float("nan")


def subset_988(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Are the people who answered the 988 question (added to the form later) different
    from everyone else? Compares recommend and retro change; Mann-Whitney U p-values."""
    df = res.df if df is None else df
    if "call_988" not in df:
        return pd.DataFrame()
    answered = df["call_988"].notna()
    ch = person_retro_change(res, df)
    parts = {"Answered 988 question": answered, "Did not answer 988 question": ~answered}
    rows = []
    for name, m in parts.items():
        g, c = df[m], ch[m]
        row = {"subset": name, "n": int(m.sum())}
        if "recommend" in g:
            r = g["recommend"].astype(float)
            n_r = int(r.notna().sum())
            row |= {"n_recommend": n_r,
                    "recommend_mean": round(r.mean(), 2) if n_r >= C.MIN_N else float("nan"),
                    "nps": round(nps(r), 1) if n_r >= C.MIN_N else float("nan")}
        n_c = int(c.notna().sum())
        row |= {"n_retro": n_c,
                "retro_change_mean": round(c.mean(), 2) if n_c >= C.MIN_N else float("nan"),
                "pct_improved": round((c.dropna() > 0).mean() * 100, 1) if n_c >= C.MIN_N else float("nan")}
        rows.append(row)
    out = pd.DataFrame(rows)
    a, b = answered, ~answered
    p = {"p_recommend": _p(mannwhitneyu, df.loc[a, "recommend"], df.loc[b, "recommend"])
         if "recommend" in df else float("nan"),
         "p_retro_change": _p(mannwhitneyu, ch[a], ch[b])}
    for k, v in p.items():
        out[k] = v  # same p on both rows (it compares the two)
    return out


def ceiling(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Share already at the top (5) before the training, who can't improve, and the
    change among everyone else."""
    df = res.df if df is None else df
    rows = []
    for rcol, lcol in res.retro_pairs.items():
        if not lcol:
            continue
        pair = df[[rcol, lcol]].dropna().astype(float)
        below = pair[pair[rcol] < 5]
        d = below[lcol] - below[rcol]
        ok = len(below) >= C.MIN_N
        rows.append({
            "item": lcol, "question_after": res.label(lcol), "n": len(pair),
            "pct_at_5_before": round((pair[rcol] == 5).mean() * 100, 1) if len(pair) >= C.MIN_N else float("nan"),
            "n_below_5_before": len(below),
            "change_mean_below_5": round(d.mean(), 2) if ok else float("nan"),
            "pct_improved_below_5": round((d > 0).mean() * 100, 1) if ok else float("nan"),
        })
    return pd.DataFrame(rows)


def trend(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Monthly n, recommend mean and retro change. Months with n < MIN_N are dropped."""
    df = res.df if df is None else df
    if "training_date" not in df or df["training_date"].isna().all():
        return pd.DataFrame()
    month = pd.to_datetime(df["training_date"]).dt.to_period("M").astype("string")
    ch = person_retro_change(res, df)
    rows = []
    for m, idx in df.groupby(month).groups.items():
        g, c = df.loc[idx], ch.loc[idx]
        if len(g) < C.MIN_N:
            continue
        n_c = int(c.notna().sum())
        n_r = int(g["recommend"].notna().sum()) if "recommend" in g else 0
        rows.append({"month": m, "n": len(g),
                     "n_recommend": n_r,
                     "recommend_mean": round(g["recommend"].astype(float).mean(), 2) if n_r >= C.MIN_N else float("nan"),
                     "n_retro": n_c,
                     "retro_change_mean": round(c.mean(), 2) if n_c >= C.MIN_N else float("nan")})
    return pd.DataFrame(rows).sort_values("month").reset_index(drop=True) if rows else pd.DataFrame()


def group_tests(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Kruskal-Wallis test of retro change across groups with n >= MIN_N.
    Pooled "Other" and "Not reported" groups are left out (they are not one group)."""
    from src.clean import NOT_REPORTED, SMALL_GROUP
    df = res.df if df is None else df
    ch = person_retro_change(res, df).rename("change")
    rows = []
    for group in ("county", "role", "language"):
        if group == "role":
            if "role_list" not in df:
                continue
            ex = df[["role_list"]].join(ch).explode("role_list").rename(columns={"role_list": "g"})
        else:
            col = f"{group}_grp"
            if col not in df:
                continue
            ex = df[[col]].join(ch).rename(columns={col: "g"})
        ex = ex.dropna(subset=["g", "change"])
        ex = ex[~ex["g"].isin([NOT_REPORTED, SMALL_GROUP, ""])]
        samples = [s["change"] for _, s in ex.groupby("g") if len(s) >= C.MIN_N]
        row = {"grouping": group, "groups_tested": len(samples),
               "n": int(sum(len(s) for s in samples)), "H": float("nan"), "p": float("nan")}
        if kruskal is not None and len(samples) >= 2:
            try:
                r = kruskal(*samples)
                row |= {"H": round(float(r.statistic), 2), "p": float(r.pvalue)}
            except ValueError:
                pass
        rows.append(row)
    return pd.DataFrame(rows)


def run_all(res: CleanResult) -> dict[str, pd.DataFrame]:
    return {
        "overall": overall(res),
        "retro_change": retro_change(res),
        "by_county": by_group(res, "county"),
        "by_role": by_group(res, "role"),
        "by_language": by_group(res, "language"),
        "subset_988": subset_988(res),
        "ceiling": ceiling(res),
        "trend_monthly": trend(res),
        "group_tests": group_tests(res),
    }


def main() -> None:
    res = load_and_clean()
    save_outputs(res)
    tables = run_all(res)
    for name, t in tables.items():
        t.to_csv(C.OUTPUT_DIR / f"{name}.csv", index=False)
    n_supp = sum(int(t["suppressed"].sum()) for k, t in tables.items()
                 if "suppressed" in t)
    print(f"Analyzed {len(res.df)} responses from {res.source_file}")
    print(f"Wrote {len(tables)} tables to {C.OUTPUT_DIR}/ ({n_supp} rows suppressed for n<{C.MIN_N})")


if __name__ == "__main__":
    main()
