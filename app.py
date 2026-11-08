"""BuildFest 2026: EveryMind 988 training survey dashboard.

Run from the repo root:
    streamlit run app.py

Reads the newest .xlsx in data/ every time that file changes, so dropping in an
updated export needs no code changes. Groups with n < MIN_N are suppressed.
"""
from __future__ import annotations

import io
import math
import zipfile

import altair as alt
import pandas as pd
import streamlit as st

from src import analyze, text_themes
from src import config as C
from src.clean import find_data_file, load_and_clean

# Validated categorical slots (colorblind-safe adjacent pair) + text ink.
BLUE, ORANGE = "#2a78d6", "#eb6834"
SMALL = f"<{C.MIN_N}"

st.set_page_config(page_title="988 Training Survey", layout="wide")


@st.cache_data(show_spinner="Cleaning survey data…")
def _load(path: str, mtime: float):
    # mtime is part of the cache key, so an updated file is re-read automatically
    return load_and_clean(path)


def bar(df, x, y, tooltip, color=BLUE, horizontal=True, x_title=None, y_title=None, domain=None):
    scale = alt.Scale(domain=domain) if domain else alt.Undefined
    enc_val = (alt.X(f"{x}:Q", title=x_title, scale=scale) if horizontal
               else alt.Y(f"{y}:Q", title=y_title, scale=scale))
    enc_cat = (alt.Y(f"{y}:N", sort="-x", title=y_title) if horizontal
               else alt.X(f"{x}:O", title=x_title))
    return (alt.Chart(df).mark_bar(color=color, cornerRadiusEnd=4)
            .encode(enc_val, enc_cat, tooltip=tooltip)
            .properties(height=alt.Step(28) if horizontal else 300))


def is_blank(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA


def hide_small_counts(t: pd.DataFrame) -> pd.DataFrame:
    """Replace any count below MIN_N in n / n_* columns with "<10"."""
    t = t.copy()
    for c in [c for c in t.columns if c == "n" or c.startswith("n_")]:
        num = pd.to_numeric(t[c], errors="coerce")
        out = num.round().astype("Int64").astype("string")
        out[num < C.MIN_N] = SMALL
        if "suppressed" in t:
            out[t["suppressed"].astype(bool)] = SMALL if c == "n" else pd.NA
        t[c] = out
    return t


def overall_safe(ov: pd.DataFrame) -> pd.DataFrame:
    """Headline table with small n's shown as "<10"."""
    ov = ov.copy()
    ov["value"] = ov["value"].astype(object)
    is_n = ov["metric"].str.contains(": n ") | (ov["metric"] == "Responses")
    small = is_n & (pd.to_numeric(ov["value"], errors="coerce") < C.MIN_N)
    ov.loc[small, "value"] = SMALL
    return ov


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
try:
    path = find_data_file()
except FileNotFoundError as e:
    st.title("988 Training Survey")
    st.error(str(e))
    st.stop()

res = _load(str(path), path.stat().st_mtime)
df_all = res.df


def lbl(col: str) -> str:
    return C.SHORT_LABELS.get(col, res.label(col))


# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #
st.sidebar.header("Filters")
st.sidebar.caption(f"Data file: `{res.source_file}` · {len(df_all):,} responses")

mask = pd.Series(True, index=df_all.index)
for col, label in [("language_grp", "Language"), ("county_grp", "County")]:
    if col in df_all:
        opts = sorted(df_all[col].dropna().unique())
        picked = st.sidebar.multiselect(label, opts)
        if picked:
            mask &= df_all[col].isin(picked)
if "role_list" in df_all:
    roles = sorted({r for rs in df_all["role_list"] for r in rs})
    picked = st.sidebar.multiselect("Role (any of)", roles)
    if picked:
        mask &= df_all["role_list"].map(lambda rs: any(r in picked for r in rs))

df = df_all[mask]
st.sidebar.info(f"Groups with fewer than **{C.MIN_N}** responses are hidden "
                "to protect anonymity and avoid unstable numbers.")

st.title("988 Training Survey")
st.caption(f"{len(df):,} responses in current view")

if len(df) < C.MIN_N:
    st.warning(f"Fewer than {C.MIN_N} responses match these filters, so results are hidden.")
    st.stop()

# Aggregate tables for the current view (also used by the download button).
ov_tbl = analyze.overall(res, df)
rc = analyze.retro_change(res, df)
group_tbls = {g: analyze.by_group(res, g, df) for g in ("county", "role", "language")}
theme_tbls = {col: text_themes.theme_summary(df[col], col) for col in res.text_cols}

tab_over, tab_retro, tab_group, tab_text, tab_quality = st.tabs(
    ["Overview", "Before vs. after", "By group", "Open-text themes", "Data quality"])

# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
with tab_over:
    ov = ov_tbl.set_index("metric")["value"]

    def tile(col, title, key, fmt, n_key=None, help=None):
        if key not in ov:
            return
        v = ov[key]
        col.metric(title, "n<10" if is_blank(v) else fmt(v), help=help)
        if n_key and n_key in ov:
            n = int(ov[n_key])
            col.caption(f"n = {n:,} answered" if n >= C.MIN_N else f"n < {C.MIN_N} answered")

    cols = st.columns(4)
    cols[0].metric("Responses", f"{int(ov['Responses']):,}")
    tile(cols[1], "Net Promoter Score", "Net Promoter Score", lambda v: f"{v:+.0f}",
         "Recommend: n answered", "% scoring 9-10 minus % scoring 0-6")
    tile(cols[2], "Likely to call 988", "Likely to call 988: % likely", lambda v: f"{v:.0f}%",
         "Likely to call 988: n answered",
         (f"Scored {C.CALL_988_LIKELY_MIN_0_10}-10 on a 0-10 scale. "
          if res.call_988_scale == "0-10" else "Likely or very likely. ")
         + "Only some respondents were asked this question.")
    tile(cols[3], "Avg. change, before → after", "Retro change: mean points (1-5 scale)",
         lambda v: f"{v:+.2f} pts", "Retro change: n with any pair",
         "Average of (after − before) across retrospective items, 1-5 scale")

    if "recommend" in df and df["recommend"].notna().sum() >= C.MIN_N:
        st.subheader("How likely to recommend the training (0-10)")
        dist = (df["recommend"].dropna().astype(int).value_counts()
                .reindex(range(11), fill_value=0).rename_axis("score").reset_index(name="count"))
        st.altair_chart(bar(dist, "score", "count", ["score", "count"], horizontal=False,
                            x_title="Score", y_title="Responses"), width="stretch")

    if res.likert_cols:
        st.subheader("% agree or strongly agree")
        lk = pd.DataFrame([{"question": lbl(c), "full question": res.label(c),
                            "pct": analyze.top_box(df[c]), "n": int(df[c].notna().sum())}
                           for c in res.likert_cols])
        shown_lk = lk[lk["n"] >= C.MIN_N]
        if len(shown_lk):
            st.altair_chart(bar(shown_lk, "pct", "question",
                                ["full question", alt.Tooltip("pct:Q", format=".1f", title="% agree"), "n"],
                                x_title="% agree", y_title=None, domain=[0, 100]), width="stretch")
        if len(shown_lk) < len(lk):
            st.caption(f"{len(lk) - len(shown_lk)} item(s) hidden because fewer than "
                       f"{C.MIN_N} people answered.")

    with st.expander("All headline numbers"):
        st.dataframe(overall_safe(ov_tbl), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# Before vs after
# --------------------------------------------------------------------------- #
with tab_retro:
    if rc.empty:
        st.info("No retrospective (before/after) item pairs were detected. "
                "Check the Data quality tab and RETRO_PAIR_OVERRIDES in src/config.py.")
    else:
        st.caption("Retrospective design: respondents rated themselves *before* the training "
                   "after it ended. Only people who answered both halves of a pair are included.")
        shown = rc[~rc["suppressed"]].assign(label=lambda d: d["item"].map(lbl))
        if shown.empty:
            st.info(f"Fewer than {C.MIN_N} people in this view answered both halves of any pair.")
        else:
            st.subheader("Average self-rating, before vs. after")
            long = shown.melt(id_vars=["label", "question_after", "n"],
                              value_vars=["before_mean", "after_mean"],
                              var_name="when", value_name="mean")
            long["when"] = long["when"].map({"before_mean": "Before", "after_mean": "After"})
            chart = (alt.Chart(long).mark_bar(cornerRadiusEnd=4)
                     .encode(x=alt.X("mean:Q", title="Mean (1 = strongly disagree, 5 = strongly agree)",
                                     scale=alt.Scale(domain=[1, 5])),
                             y=alt.Y("label:N", title=None),
                             yOffset=alt.YOffset("when:N", sort=["Before", "After"]),
                             color=alt.Color("when:N", sort=["Before", "After"], title=None,
                                             scale=alt.Scale(domain=["Before", "After"],
                                                             range=[ORANGE, BLUE]),
                                             legend=alt.Legend(orient="top")),
                             tooltip=[alt.Tooltip("question_after:N", title="question"), "when",
                                      alt.Tooltip("mean:Q", format=".2f"), "n"])
                     .properties(height=alt.Step(18)))
            st.altair_chart(chart, width="stretch")

            st.subheader("% who rated themselves higher after than before")
            st.altair_chart(bar(shown, "pct_improved", "label",
                                [alt.Tooltip("question_after:N", title="question"),
                                 alt.Tooltip("pct_improved:Q", format=".1f", title="% improved"),
                                 alt.Tooltip("pct_same:Q", format=".1f", title="% same"),
                                 alt.Tooltip("pct_declined:Q", format=".1f", title="% lower"), "n"],
                                x_title="% improved", y_title=None, domain=[0, 100]),
                            width="stretch")
            st.caption("People already at 5 before the training cannot improve on that item.")
        n_hidden = int(rc["suppressed"].sum())
        if n_hidden:
            st.caption(f"{n_hidden} item(s) hidden because n < {C.MIN_N}.")
        st.dataframe(hide_small_counts(rc.drop(columns=["item"])), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# By group
# --------------------------------------------------------------------------- #
METRIC_NAMES = {"recommend_mean": "Recommend: mean (0-10)", "nps": "Net Promoter Score",
                "pct_likely_988": "% likely to call 988",
                "retro_change_mean": "Avg. change, before → after (pts)"}
METRIC_N = {"recommend_mean": "n_recommend", "nps": "n_recommend",
            "pct_likely_988": "n_988", "retro_change_mean": "n_retro"}

with tab_group:
    g1, g2 = st.columns(2)
    group = g1.selectbox("Group by", ["county", "role", "language"])
    tbl = group_tbls[group]
    if tbl.empty:
        st.info(f"No {group} column was detected.")
    else:
        metric_cols = [c for c in tbl.columns
                       if c not in ("group", "n", "suppressed") and not c.startswith("n_")]
        nice = {c: (f"% agree: {lbl(c.removeprefix('pct_agree_'))}" if c.startswith("pct_agree_")
                    else METRIC_NAMES.get(c, c)) for c in metric_cols}
        by_name = {v: k for k, v in nice.items()}
        metric = by_name[g2.selectbox("Metric", list(by_name))]
        n_col = (f"n_agree_{metric.removeprefix('pct_agree_')}" if metric.startswith("pct_agree_")
                 else METRIC_N.get(metric))
        if n_col not in tbl:
            n_col = "n"
        visible = tbl[~tbl["suppressed"] & tbl[metric].notna()]
        if visible.empty:
            st.info(f"No {group} has at least {C.MIN_N} people who answered this question.")
        else:
            st.altair_chart(bar(visible, metric, "group",
                                ["group", alt.Tooltip(f"{metric}:Q", format=".2f", title=nice[metric]),
                                 alt.Tooltip(f"{n_col}:Q", title="n answered"),
                                 alt.Tooltip("n:Q", title="n in group")],
                                x_title=nice[metric], y_title=None), width="stretch")
        n_small_grp = int(tbl["suppressed"].sum())
        n_small_metric = int((~tbl["suppressed"] & tbl[metric].isna()).sum())
        notes = []
        if n_small_grp:
            notes.append(f"{n_small_grp} group(s) hidden because the group has n < {C.MIN_N}")
        if n_small_metric:
            notes.append(f"{n_small_metric} more hidden because fewer than {C.MIN_N} "
                         "in the group answered this question")
        if notes:
            st.caption("; ".join(notes) + ".")
        st.caption(f"Bars use only people who answered this question (`{n_col}` in the table).")
        if group == "role":
            st.caption("Respondents who chose several roles are counted in each.")
        display = hide_small_counts(tbl)
        st.dataframe(display.rename(columns=nice), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# Open-text themes
# --------------------------------------------------------------------------- #
with tab_text:
    if not res.text_cols:
        st.info("No open-text columns were detected.")
    st.caption("Keyword-based coding (src/text_themes.py). One response can match several "
               "themes. Validate by hand-reading a sample before quoting any number.")
    for col, th in theme_tbls.items():
        st.subheader(res.label(col))
        n_ans = int(th["n_answered"].iloc[0]) if len(th) else 0
        if n_ans < C.MIN_N:
            st.info(f"Fewer than {C.MIN_N} people in this view answered this question.")
            continue
        shown_th = th[~th["under_min_n"]]
        if len(shown_th):
            st.altair_chart(bar(shown_th, "pct_of_answered", "theme",
                                ["theme", "count",
                                 alt.Tooltip("pct_of_answered:Q", format=".1f", title="% of answered")],
                                x_title="% of people who answered", y_title=None),
                            width="stretch")
        n_hidden = int(th["under_min_n"].sum())
        st.caption(f"{n_ans:,} people answered."
                   + (f" {n_hidden} theme(s) with fewer than {C.MIN_N} mentions hidden."
                      if n_hidden else ""))

# --------------------------------------------------------------------------- #
# Data quality
# --------------------------------------------------------------------------- #
with tab_quality:
    st.markdown("How the raw file was interpreted. **Check the column detection and "
                "retrospective pairs** before trusting any result.")
    st.code("\n".join(res.report), language=None)

# --------------------------------------------------------------------------- #
# Download: aggregate tables only (never row-level data or open text)
# --------------------------------------------------------------------------- #
def summary_zip() -> bytes:
    tables = {"overall.csv": overall_safe(ov_tbl)}
    if not rc.empty:
        tables["retro_change.csv"] = hide_small_counts(rc)
    for g, t in group_tbls.items():
        if not t.empty:
            tables[f"by_{g}.csv"] = hide_small_counts(t)
    for col, th in theme_tbls.items():
        if len(th) and int(th["n_answered"].iloc[0]) >= C.MIN_N:
            tables[f"themes_{col}.csv"] = th[~th["under_min_n"]].drop(columns="under_min_n")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, t in tables.items():
            z.writestr(name, t.to_csv(index=False))
    return buf.getvalue()


st.sidebar.download_button(
    "Download summary tables (CSV)", data=summary_zip(), file_name="summary_tables.zip",
    mime="application/zip",
    help=f"Aggregate tables for the current filters only. Groups and counts under {C.MIN_N} "
         "are hidden. No individual responses are included.")
