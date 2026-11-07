"""BuildFest 2026: EveryMind 988 training survey dashboard.

Run from the repo root:
    streamlit run app.py

Reads the newest .xlsx in data/ every time that file changes, so dropping in an
updated export needs no code changes. Groups with n < MIN_N are suppressed.
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src import analyze, text_themes
from src import config as C
from src.clean import find_data_file, load_and_clean

# Validated categorical slots (colorblind-safe adjacent pair) + text ink.
BLUE, ORANGE = "#2a78d6", "#eb6834"

st.set_page_config(page_title="988 Training Survey", layout="wide")


@st.cache_data(show_spinner="Cleaning survey data…")
def _load(path: str, mtime: float):
    # mtime is part of the cache key, so an updated file is re-read automatically
    return load_and_clean(path)


def bar(df, x, y, tooltip, color=BLUE, horizontal=True, x_title=None, y_title=None):
    enc_val = alt.X(f"{x}:Q", title=x_title) if horizontal else alt.Y(f"{y}:Q", title=y_title)
    enc_cat = (alt.Y(f"{y}:N", sort="-x", title=y_title) if horizontal
               else alt.X(f"{x}:O", title=x_title))
    return (alt.Chart(df).mark_bar(color=color, cornerRadiusEnd=4)
            .encode(enc_val, enc_cat, tooltip=tooltip)
            .properties(height=alt.Step(28) if horizontal else 300))


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

tab_over, tab_retro, tab_group, tab_text, tab_quality = st.tabs(
    ["Overview", "Before vs. after", "By group", "Open-text themes", "Data quality"])

# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
with tab_over:
    ov = analyze.overall(res, df).set_index("metric")["value"]
    cols = st.columns(4)
    cols[0].metric("Responses", f"{int(ov['Responses']):,}")
    if "Net Promoter Score" in ov:
        cols[1].metric("Net Promoter Score", f"{ov['Net Promoter Score']:+.0f}",
                       help="% scoring 9-10 minus % scoring 0-6")
    if "Likely to call 988: % likely" in ov:
        cols[2].metric("Likely to call 988", f"{ov['Likely to call 988: % likely']:.0f}%",
                       help=f"n = {int(ov['Likely to call 988: n answered'])} answered. "
                            + (f"Scored {C.CALL_988_LIKELY_MIN_0_10}-10 on a 0-10 scale."
                               if res.call_988_scale == "0-10" else "Likely or very likely."))
    if "Retro change: mean points (1-5 scale)" in ov:
        cols[3].metric("Avg. change, before → after",
                       f"{ov['Retro change: mean points (1-5 scale)']:+.2f} pts",
                       help="Average of (after − before) across retrospective items, 1-5 scale")

    if "recommend" in df:
        st.subheader("How likely to recommend the training (0-10)")
        dist = (df["recommend"].dropna().astype(int).value_counts()
                .reindex(range(11), fill_value=0).rename_axis("score").reset_index(name="count"))
        st.altair_chart(bar(dist, "score", "count", ["score", "count"], horizontal=False,
                            x_title="Score", y_title="Responses"), width="stretch")

    if res.likert_cols:
        st.subheader("% agree or strongly agree")
        lk = pd.DataFrame([{"question": res.label(c), "pct": analyze.top_box(df[c]),
                            "n": int(df[c].notna().sum())} for c in res.likert_cols])
        st.altair_chart(bar(lk, "pct", "question", ["question", alt.Tooltip("pct:Q", format=".1f"), "n"],
                            x_title="% agree", y_title=None), width="stretch")

    with st.expander("All headline numbers"):
        st.dataframe(analyze.overall(res, df), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# Before vs after
# --------------------------------------------------------------------------- #
with tab_retro:
    rc = analyze.retro_change(res, df)
    if rc.empty:
        st.info("No retrospective (before/after) item pairs were detected. "
                "Check the Data quality tab and RETRO_PAIR_OVERRIDES in src/config.py.")
    else:
        st.caption("Retrospective design: respondents rated themselves *before* the training "
                   "after it ended. Only people who answered both halves of a pair are included.")
        shown = rc[~rc["suppressed"]]
        long = shown.melt(id_vars=["question_after", "n"], value_vars=["before_mean", "after_mean"],
                          var_name="when", value_name="mean")
        long["when"] = long["when"].map({"before_mean": "Before", "after_mean": "After"})
        chart = (alt.Chart(long).mark_bar(cornerRadiusEnd=4)
                 .encode(x=alt.X("mean:Q", title="Mean (1 = strongly disagree, 5 = strongly agree)",
                                 scale=alt.Scale(domain=[1, 5])),
                         y=alt.Y("question_after:N", title=None),
                         yOffset=alt.YOffset("when:N", sort=["Before", "After"]),
                         color=alt.Color("when:N", sort=["Before", "After"], title=None,
                                         scale=alt.Scale(domain=["Before", "After"], range=[ORANGE, BLUE]),
                                         legend=alt.Legend(orient="top")),
                         tooltip=["question_after", "when", alt.Tooltip("mean:Q", format=".2f"), "n"])
                 .properties(height=alt.Step(18)))
        st.altair_chart(chart, width="stretch")
        st.dataframe(rc.drop(columns=["item"]), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# By group
# --------------------------------------------------------------------------- #
with tab_group:
    g1, g2 = st.columns(2)
    group = g1.selectbox("Group by", ["county", "role", "language"])
    tbl = analyze.by_group(res, group, df)
    if tbl.empty:
        st.info(f"No {group} column was detected.")
    else:
        metric_cols = [c for c in tbl.columns
                       if c not in ("group", "n", "suppressed") and not c.startswith("n_")]
        nice = {c: (f"% agree: {res.label(c.removeprefix('pct_agree_'))}" if c.startswith("pct_agree_")
                    else c) for c in metric_cols}
        metric = g2.selectbox("Metric", metric_cols, format_func=nice.get)
        visible = tbl[~tbl["suppressed"]]
        st.altair_chart(bar(visible, metric, "group", ["group", alt.Tooltip(f"{metric}:Q", format=".2f"), "n"],
                            x_title=nice[metric], y_title=None), width="stretch")
        n_hidden = int(tbl["suppressed"].sum())
        if n_hidden:
            st.caption(f"{n_hidden} group(s) hidden because n < {C.MIN_N}.")
        if group == "role":
            st.caption("Respondents who chose several roles are counted in each.")
        display = tbl.copy()
        display.loc[display["suppressed"], "n"] = pd.NA
        display["n"] = display["n"].astype("string").fillna(f"<{C.MIN_N}")
        st.dataframe(display.rename(columns=nice), hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# Open-text themes
# --------------------------------------------------------------------------- #
with tab_text:
    if not res.text_cols:
        st.info("No open-text columns were detected.")
    st.caption("Keyword-based coding (src/text_themes.py). One response can match several "
               "themes. Validate by hand-reading a sample before quoting any number.")
    for col in res.text_cols:
        st.subheader(res.label(col))
        th = text_themes.theme_summary(df[col], col)
        st.altair_chart(bar(th, "pct_of_answered", "theme",
                            ["theme", "count", alt.Tooltip("pct_of_answered:Q", format=".1f")],
                            x_title="% of people who answered", y_title=None),
                        width="stretch")
        st.caption(f"{int(th['n_answered'].iloc[0]):,} people answered.")

# --------------------------------------------------------------------------- #
# Data quality
# --------------------------------------------------------------------------- #
with tab_quality:
    st.markdown("How the raw file was interpreted. **Check the column detection and "
                "retrospective pairs** before trusting any result.")
    st.code("\n".join(res.report), language=None)
