"""988 Training Insights: dashboard for EveryMind's 988 training survey.

Run from the repo root:
    streamlit run app.py          (or double-click start_dashboard.command / .bat)

Data: the newest .xlsx in data/, or a file uploaded in the sidebar (read in memory,
never saved). A new export needs no code changes. Every number shown is an
aggregate; any group or metric answered by fewer than MIN_N people is hidden.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import inspect
import io
import math
import sys
import zipfile
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))  # find src/ on every Streamlit version
from src import analyze, insights, text_themes  # noqa: E402
from src import config as C  # noqa: E402
from src.clean import NOT_REPORTED, find_data_file, load_and_clean  # noqa: E402

ROOT = Path(__file__).resolve().parent
SMALL = f"<{C.MIN_N}"
# Colorblind-validated categorical colors (see docs/METHODS.md, "Charts").
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#a3a19a"
AUDIENCE_COLORS = {"Students": "#6250d6", "Adults": "#1baf7a"}
NPS_COLORS = {"Detractor (0-6)": "#b7d3f6", "Passive (7-8)": "#5598e7", "Promoter (9-10)": "#184f95"}

st.set_page_config(page_title="988 Training Insights", layout="wide")


def _theme_type() -> str | None:
    """'light' / 'dark' as the viewer currently sees the app (None if unknown)."""
    try:
        t = getattr(getattr(st.context, "theme", None), "type", None)
        return t if t in ("light", "dark") else None
    except Exception:  # noqa: BLE001 - older Streamlit
        return None


# Value labels must read on the chart background: near-white on dark, near-black on light,
# mid-gray (readable on both, 3:1+) when the theme isn't known yet.
LABEL_INK = {"dark": "#e8e7e1", "light": "#2b2b29"}.get(_theme_type(), "#8a8984")
st.markdown("""<style>
div[data-testid="stMetricValue"] {font-size: 1.9rem;}
div[data-testid="stCaptionContainer"] p {margin-bottom: 0.2rem;}
</style>""", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Reading and cleaning the survey…")
def load_from_path(path: str, mtime: float):
    return load_and_clean(path)  # mtime is in the cache key so an updated file reloads


@st.cache_data(show_spinner="Reading and cleaning the uploaded file…")
def load_from_upload(data: bytes, name: str):
    return load_and_clean(data, name=name)


def welcome() -> None:
    st.title("988 Training Insights")
    st.info("No survey file found yet.")
    st.markdown(f"""
**To get started, either:**
1. Upload the Microsoft Forms export (.xlsx or .csv) with **Use a different survey export** in the sidebar, or
2. Save the export into the `data/` folder (`{C.DATA_DIR}`) and refresh this page.

The file is read on this computer only. See *README.md → Updating the data* for how to export it.
""")
    st.stop()


st.sidebar.title("988 Training Insights")
upload = st.sidebar.file_uploader(
    "Use a different survey export (.xlsx or .csv)", type=["xlsx", "csv"],
    help="Optional. The file is read in memory on this computer and never saved. "
         "Without an upload, the newest .xlsx/.csv in the data/ folder is used.")
try:
    if upload is not None:
        raw = upload.getvalue()
        data_key = ("upload", upload.name, hashlib.sha1(raw).hexdigest())  # identifies the data for caching
        res = load_from_upload(raw, upload.name)
    else:
        try:
            path = find_data_file()
        except FileNotFoundError:
            welcome()
        data_key = ("file", str(path), path.stat().st_mtime)
        res = load_from_path(*data_key[1:])
except Exception as e:  # noqa: BLE001 - show a friendly message instead of a traceback
    st.title("988 Training Insights")
    st.error("This file could not be read as a 988 training survey export. Check that it is the "
             "Microsoft Forms export (.xlsx or .csv, one row per response).")
    with st.expander("Technical details"):
        st.code(f"{type(e).__name__}: {e}")
    st.stop()

df_all = res.df
if "audience" not in df_all:  # export without a role question: one audience for everyone
    df_all = df_all.assign(audience="All respondents")


def lbl(col: str) -> str:
    return C.SHORT_LABELS.get(col, res.label(col))


def is_blank(v) -> bool:
    return v is None or v is pd.NA or (isinstance(v, float) and math.isnan(v))


def n_txt(n) -> str:
    return SMALL if is_blank(n) or n < C.MIN_N else f"{int(n):,}"


# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #
st.sidebar.header("Filters")
mask = pd.Series(True, index=df_all.index)
active: list[str] = []     # human-readable description of each filter in use
filter_key: list = []      # the same, hashable, for caching results per filter combination


def pick(col: str, label: str, help: str | None = None) -> None:
    global mask
    if col not in df_all:
        return
    opts = sorted(df_all[col].dropna().unique())
    chosen = st.sidebar.multiselect(label, opts, help=help)
    if chosen:
        mask &= df_all[col].isin(chosen)
        active.append(f"{label}: {', '.join(map(str, chosen))}")
        filter_key.append((col, tuple(map(str, chosen))))


pick("audience", "Audience", "Students = anyone whose role includes 'Student'; everyone else is Adults.")
pick("language_grp", "Survey language")
pick("county_grp", "County", f"Counties with fewer than {C.MIN_N} responses are pooled as '{SMALL} other'.")
if "role_list" in df_all:
    roles = sorted({r for rs in df_all["role_list"] for r in rs})
    chosen = st.sidebar.multiselect("Role (any of)", roles)
    if chosen:
        mask &= df_all["role_list"].map(lambda rs: any(r in chosen for r in rs))
        active.append(f"Role: {', '.join(chosen)}")
        filter_key.append(("role", tuple(chosen)))
if "training_date" in df_all and df_all["training_date"].notna().any():
    d_min, d_max = df_all["training_date"].min().date(), df_all["training_date"].max().date()
    rng = st.sidebar.date_input("Training dates", (d_min, d_max), min_value=d_min, max_value=d_max)
    if isinstance(rng, (list, tuple)) and len(rng) == 2 and (rng[0], rng[1]) != (d_min, d_max):
        mask &= df_all["training_date"].dt.date.between(rng[0], rng[1])
        active.append(f"Training dates: {rng[0]:%b %d, %Y} to {rng[1]:%b %d, %Y}")
        filter_key.append(("date", rng[0].isoformat(), rng[1].isoformat()))

df = df_all[mask]
filter_key = tuple(filter_key)
filters_text = "; ".join(active) if active else "None (all responses)"
st.sidebar.caption(f"Data: **{res.source_file}** · {len(df_all):,} responses "
                   f"({len(df):,} in current view)")
st.sidebar.info(f"**Privacy:** any group or number based on fewer than {C.MIN_N} people is hidden "
                f"and shown as “{SMALL}”. No individual responses are displayed or downloadable.")

if len(df) < C.MIN_N:
    st.title("988 Training Insights")
    st.warning(f"Fewer than {C.MIN_N} responses match these filters ({filters_text}), so results are "
               "hidden. Remove a filter to see results.")
    st.stop()


# Cached per data file + filter combination, so switching tabs or widgets doesn't redo the
# whole analysis. Arguments starting with "_" are not hashed; the keys identify them.
@st.cache_data(show_spinner="Calculating results…", max_entries=50)
def compute(key_data: tuple, key_filters: tuple, _res, _df: pd.DataFrame):
    return analyze.run_all(_res, _df), text_themes.run_all(_res, _df)


tables, themes = compute(data_key, filter_key, res, df)
ov = tables["overall"].set_index("metric")["value"]


# --------------------------------------------------------------------------- #
# Chart helpers
# --------------------------------------------------------------------------- #
def hbar(data: pd.DataFrame, x: str, y: str, *, title: str, tooltip: list, color: str = BLUE,
         domain=None, fmt: str = ".0f", suffix: str = "", sort="-x", color_map: dict | None = None
         ) -> alt.LayerChart:
    """Horizontal bars with a direct value label at the end of each bar. color_map
    colors each bar by its category (the axis label names it, so no legend)."""
    base = alt.Chart(data).encode(y=alt.Y(f"{y}:N", sort=sort, title=None, axis=alt.Axis(labelLimit=360)))
    scale = alt.Scale(domain=domain) if domain else alt.Undefined
    enc = dict(x=alt.X(f"{x}:Q", title=title, scale=scale), tooltip=tooltip)
    if color_map:
        enc["color"] = alt.Color(f"{y}:N", legend=None, scale=alt.Scale(
            domain=list(color_map), range=list(color_map.values())))
    bars = base.mark_bar(color=color, cornerRadiusEnd=4).encode(**enc)
    text = base.mark_text(align="left", baseline="middle", dx=4, color=LABEL_INK).transform_calculate(
        _label=f"format(datum['{x}'], '{fmt}') + '{suffix}'").encode(x=f"{x}:Q", text="_label:N")
    return (bars + text).properties(height=alt.Step(30))


def grouped_hbar(data: pd.DataFrame, x: str, y: str, series: str, colors: dict, *, title: str,
                 tooltip: list, domain=None, fmt: str = ".0f", suffix: str = "", sort=None) -> alt.LayerChart:
    order = list(colors)
    base = alt.Chart(data).encode(
        y=alt.Y(f"{y}:N", title=None, sort=sort, axis=alt.Axis(labelLimit=360)),
        yOffset=alt.YOffset(f"{series}:N", sort=order))
    scale = alt.Scale(domain=domain) if domain else alt.Undefined
    bars = base.mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X(f"{x}:Q", title=title, scale=scale),
        color=alt.Color(f"{series}:N", title=None, sort=order,
                        scale=alt.Scale(domain=order, range=[colors[k] for k in order]),
                        legend=alt.Legend(orient="top")),
        tooltip=tooltip)
    text = base.mark_text(align="left", baseline="middle", dx=4, fontSize=11, color=LABEL_INK).transform_calculate(
        _label=f"format(datum['{x}'], '{fmt}') + '{suffix}'").encode(x=f"{x}:Q", text="_label:N")
    return (bars + text).properties(height=alt.Step(17))


def lines(data: pd.DataFrame, x: str, y: str, series: str, colors: dict, *, title: str,
          tooltip: list, domain=None) -> alt.LayerChart:
    order = [k for k in colors if k in set(data[series])]
    scale = alt.Scale(domain=domain) if domain else alt.Scale(zero=False)
    enc = dict(x=alt.X(f"{x}:O", title=None, axis=alt.Axis(labelAngle=0)),
               y=alt.Y(f"{y}:Q", title=title, scale=scale),
               color=alt.Color(f"{series}:N", title=None, sort=order,
                               scale=alt.Scale(domain=order, range=[colors[k] for k in order]),
                               legend=alt.Legend(orient="top")))
    line = alt.Chart(data).mark_line(strokeWidth=2).encode(**enc)
    pts = alt.Chart(data).mark_point(size=70, filled=True).encode(**enc, tooltip=tooltip)
    return (line + pts).properties(height=320)


_CHART_HAS_WIDTH = "width" in inspect.signature(st.altair_chart).parameters


def show(chart) -> None:
    # Streamlit >= 1.5x uses width="stretch"; 1.50 (newest for Python 3.9) uses use_container_width.
    if _CHART_HAS_WIDTH:
        st.altair_chart(chart, width="stretch")
    else:
        st.altair_chart(chart, use_container_width=True)


def p_text(p) -> str:
    return "" if is_blank(p) else ("p < 0.001" if p < 0.001 else f"p = {p:.3f}")


# --------------------------------------------------------------------------- #
# Header + tabs
# --------------------------------------------------------------------------- #
st.title("988 Training Insights")
dates = df["training_date"].dropna() if "training_date" in df else pd.Series(dtype="datetime64[ns]")
st.caption(f"{len(df):,} responses"
           + (f" · trainings from {dates.min():%b %d, %Y} to {dates.max():%b %d, %Y}" if len(dates) else "")
           + " · Retrospective survey: participants rated themselves before and after, at the end of the training.")
if active:
    st.info(f"**Filtered view:** {filters_text}. Every number below describes only these "
            f"{len(df):,} of {len(df_all):,} responses, and so does the download.")

# One source for the tab guide (Summary tab) and each tab's opening line.
TAB_GUIDE = {
    "Summary": ("Is the training working, and what should we do next?",
                "Headline numbers and plain-language takeaways with suggested actions."),
    "Knowledge gains": ("Did participants learn what the training teaches?",
                        "Agreement with each knowledge statement before vs. after, and how individuals moved."),
    "Intent to call 988": ("Will knowledge turn into action?",
                           "How likely people are to call 988, and how that links to what they know."),
    "Audiences & communities": ("Who does the training work less well for?",
                                "Results by audience, county, role and language, with significance tests."),
    "Trends & sessions": ("Is quality holding up, and which sessions need follow-up?",
                          "Results over time, and a scorecard that flags individual training sessions."),
    "Participant voice": ("What do participants value, and what would they change?",
                          "Themes in the two open-ended questions, overall or students vs. adults."),
    "Data quality & methods": ("Can these numbers be trusted?",
                               "Data checks, robustness tests, how the file was read, and definitions."),
}


def intro(tab: str) -> None:
    q, what = TAB_GUIDE[tab]
    st.markdown(f"**{q}** {what}")


tabs = st.tabs(list(TAB_GUIDE))

# ---- Summary ------------------------------------------------------------------
with tabs[0]:
    with st.expander("**Guide: what each tab shows**", expanded=True):
        st.markdown("| Tab | Question it answers | What you'll find |\n|---|---|---|\n" + "\n".join(
            f"| **{t}** | {q} | {w} |" for t, (q, w) in TAB_GUIDE.items()))
        st.caption(f"Use the sidebar to filter by audience, language, county, role or date, to upload a new "
                   f"export, or to download a summary. Anything based on fewer than {C.MIN_N} people is hidden; "
                   f"results from {C.MIN_N}–{C.THIN_N - 1} people are marked *thin* (indicative only).")
    c = st.columns(5)
    c[0].metric("Responses", f"{len(df):,}")
    after = ov.get("Knowledge: % agree after (avg of outcome items)")
    before = ov.get("Knowledge: % agree before (avg, retrospective)")
    if not is_blank(after):
        c[1].metric("Knowledge after training", f"{after:.0f}% agree",
                    delta=None if is_blank(before) else f"{after - before:+.0f} pts vs. before",
                    help="Average % agreeing with the knowledge statements (identify crises, describe "
                         "988, know when to use it). 'Before' is the retrospective self-rating.")
    imp = ov.get("Retro change: % who improved on average")
    if not is_blank(imp):
        c[2].metric("Rated themselves higher", f"{imp:.0f}%",
                    help="Share whose average after-rating is above their before-rating.")
    nps_v = ov.get("Net Promoter Score")
    c[3].metric("Net Promoter Score", "n<10" if is_blank(nps_v) else f"{nps_v:+.0f}",
                help="% scoring 9-10 minus % scoring 0-6 on 'How likely are you to recommend…'. "
                     "Ranges from -100 to +100.")
    c[3].caption(f"n = {n_txt(ov.get('Recommend: n answered'))}")
    p988 = ov.get("Likely to call 988: % likely")
    c[4].metric("Likely to call 988", "n<10" if is_blank(p988) else f"{p988:.0f}%",
                help=(f"Scored {C.CALL_988_LIKELY_MIN_0_10}-10 on the 0-10 question. "
                      if res.call_988_scale == "0-10" else "Likely or very likely. ")
                + "Only some respondents answered this question.")
    n988_v = ov.get('Likely to call 988: n answered')
    c[4].caption(f"n = {n_txt(n988_v)}" + (" · thin" if not is_blank(n988_v) and C.MIN_N <= n988_v < C.THIN_N else ""))

    st.subheader("What the data says")
    items = insights.build(res, tables, themes, label=lbl)
    st.markdown(insights.to_markdown(items) if items else "_Not enough data in this view._")
    st.caption("Written automatically from the tables in this dashboard, so it updates with new data and "
               f"with your filters. Uses only groups of {C.MIN_N}+ people; *thin* = fewer than {C.THIN_N}. "
               "Suggested actions are starting points for staff discussion, not conclusions.")

    left, right = st.columns(2)
    rc = tables["retro_change"]
    if not rc.empty and (~rc["suppressed"]).any():
        r = rc[~rc["suppressed"]].assign(item_label=lambda d: d["item"].map(lbl))
        long = r.melt(id_vars=["item_label", "n"], value_vars=["top_box_before", "top_box_after"],
                      var_name="when", value_name="pct")
        long["when"] = long["when"].map({"top_box_before": "Before", "top_box_after": "After"})
        with left:
            st.markdown("**% who agree, before vs. after the training**")
            show(grouped_hbar(long, "pct", "item_label", "when", {"Before": ORANGE, "After": BLUE},
                              title="% agree or strongly agree", domain=[0, 100], suffix="%",
                              tooltip=["item_label", "when", alt.Tooltip("pct:Q", format=".1f"), "n"]))
    if "nps_group" in df and "audience" in df:
        nps_rows = []
        for aud, g in df.groupby("audience", observed=True):
            s = g["nps_group"].dropna()
            if len(s) >= C.MIN_N and aud != NOT_REPORTED:
                for cat, k in zip(["Detractor", "Passive", "Promoter"], list(NPS_COLORS)):
                    nps_rows.append({"audience": f"{aud} (n={len(s):,})", "category": k,
                                     "pct": (s == cat).mean() * 100})
        if nps_rows:
            nd = pd.DataFrame(nps_rows)
            with right:
                st.markdown("**Would they recommend the training? (0-10)**")
                chart = alt.Chart(nd).mark_bar().encode(
                    x=alt.X("pct:Q", stack="normalize", title="% of respondents", axis=alt.Axis(format="%")),
                    y=alt.Y("audience:N", title=None),
                    color=alt.Color("category:N", title=None, sort=list(NPS_COLORS),
                                    scale=alt.Scale(domain=list(NPS_COLORS), range=list(NPS_COLORS.values())),
                                    legend=alt.Legend(orient="top")),
                    order=alt.Order("category:N", sort="ascending"),
                    tooltip=["audience", "category", alt.Tooltip("pct:Q", format=".1f", title="%")]
                ).properties(height=alt.Step(40))
                show(chart)

# ---- Knowledge gains ----------------------------------------------------------------
with tabs[1]:
    intro("Knowledge gains")
    st.caption("Each person rated each statement for *after* and, looking back, for *before* the training.")
    rc = tables["retro_change"]
    if rc.empty:
        st.info("No before/after question pairs were found in this file (see Data quality & methods).")
    else:
        split = st.toggle("Compare students and adults", value=False, key="k_split")
        if split and "audience" in df:
            parts = []
            for aud, g in df.groupby("audience", observed=True):
                if aud == NOT_REPORTED:
                    continue
                t = analyze.retro_change(res, g)
                t = t[~t["suppressed"]]
                if len(t):
                    parts.append(t.assign(audience=aud))
            if parts:
                t = pd.concat(parts)
                t["item_label"] = t["item"].map(lbl)
                long = t.melt(id_vars=["item_label", "audience", "n"],
                              value_vars=["top_box_before", "top_box_after"], var_name="when", value_name="pct")
                long["series"] = long["audience"] + " · " + long["when"].map(
                    {"top_box_before": "before", "top_box_after": "after"})
                colors = {"Students · before": "#b1a8ec", "Students · after": AUDIENCE_COLORS["Students"],
                          "Adults · before": "#9fdcc4", "Adults · after": AUDIENCE_COLORS["Adults"]}
                show(grouped_hbar(long, "pct", "item_label", "series", colors, title="% agree",
                                  domain=[0, 100], suffix="%",
                                  tooltip=["item_label", "series", alt.Tooltip("pct:Q", format=".1f"), "n"]))
        else:
            r = rc[~rc["suppressed"]].assign(item_label=lambda d: d["item"].map(lbl))
            long = r.melt(id_vars=["item_label", "n"], value_vars=["top_box_before", "top_box_after"],
                          var_name="when", value_name="pct")
            long["when"] = long["when"].map({"top_box_before": "Before", "top_box_after": "After"})
            show(grouped_hbar(long, "pct", "item_label", "when", {"Before": ORANGE, "After": BLUE},
                              title="% agree or strongly agree", domain=[0, 100], suffix="%",
                              tooltip=["item_label", "when", alt.Tooltip("pct:Q", format=".1f"), "n"]))
        st.markdown("**How individuals moved**")
        r = rc[~rc["suppressed"]].assign(item_label=lambda d: d["item"].map(lbl))
        mv = r.melt(id_vars=["item_label", "n"], value_vars=["pct_improved", "pct_same", "pct_declined"],
                    var_name="move", value_name="pct")
        mv["move"] = mv["move"].map({"pct_improved": "Rated higher", "pct_same": "Same",
                                     "pct_declined": "Rated lower"})
        show(alt.Chart(mv).mark_bar().encode(
            x=alt.X("pct:Q", stack="normalize", title="% of people", axis=alt.Axis(format="%")),
            y=alt.Y("item_label:N", title=None, axis=alt.Axis(labelLimit=360)),
            color=alt.Color("move:N", title=None, sort=["Rated higher", "Same", "Rated lower"],
                            scale=alt.Scale(domain=["Rated higher", "Same", "Rated lower"],
                                            range=[BLUE, GRAY, ORANGE]), legend=alt.Legend(orient="top")),
            order=alt.Order("move:N"),
            tooltip=["item_label", "move", alt.Tooltip("pct:Q", format=".1f", title="%"), "n"],
        ).properties(height=alt.Step(36)))
        ce = tables.get("ceiling", pd.DataFrame())
        if not ce.empty:
            ce_txt = ", ".join(f"{lbl(r_['item'])}: {r_['pct_at_5_before']:.0f}%" for _, r_ in ce.iterrows()
                               if not is_blank(r_["pct_at_5_before"]))
            st.caption(f"Already at the top (5) before the training, so they could not rate higher: {ce_txt}.")
        st.markdown("**Detail table**")
        show_cols = {"item": "Item", "n": "n", "top_box_before": "% agree before", "top_box_after": "% agree after",
                     "before_mean": "Mean before (1-5)", "after_mean": "Mean after (1-5)", "change": "Mean change",
                     "pct_improved": "% rated higher", "pct_declined": "% rated lower", "wilcoxon_p": "Wilcoxon p"}
        t = analyze.safe_table(rc)[list(show_cols)].rename(columns=show_cols)
        t["Item"] = rc["item"].map(lbl)
        t["Wilcoxon p"] = rc["wilcoxon_p"].map(p_text)
        st.dataframe(t, hide_index=True, width="stretch")
        st.caption("Wilcoxon signed-rank test: is the before → after change larger than chance? "
                   "Self-reported and retrospective, so it measures perceived learning, not a test score.")

# ---- Intent to call 988 ----------------------------------------------------------------
with tabs[2]:
    intro("Intent to call 988")
    if "call_988" not in df:
        st.info("This file has no 'likely to call 988' question.")
    else:
        n988 = int(df["call_988"].notna().sum())
        st.markdown(f"**{n988:,} of {len(df):,}** respondents in this view ({n988 / len(df) * 100:.0f}%) answered "
                    "*How likely are you to call 988 if you or someone else is experiencing a mental health "
                    "challenge or crisis?* All results here describe only those people.")
        if n988 < C.MIN_N:
            st.warning(f"Fewer than {C.MIN_N} people answered, so results are hidden.")
        else:
            left, right = st.columns(2)
            with left:
                st.markdown("**How likely are they to call?**")
                if res.call_988_scale == "0-10":
                    bands = pd.cut(df["call_988"].astype(float), [-0.1, 4, 6, 8, 10],
                                   labels=["0-4 (unlikely)", "5-6", "7-8", "9-10 (very likely)"])
                    rows = []
                    for aud, g in df.assign(band=bands).groupby("audience", observed=True):
                        s = g["band"].dropna()
                        if len(s) >= C.MIN_N and aud != NOT_REPORTED:
                            for b, k in s.value_counts().items():
                                rows.append({"audience": f"{aud} (n={len(s)})", "band": str(b),
                                             "pct": k / len(s) * 100, "k": k})
                    bd = pd.DataFrame(rows)
                    if len(bd):
                        order = ["0-4 (unlikely)", "5-6", "7-8", "9-10 (very likely)"]
                        show(alt.Chart(bd).mark_bar().encode(
                            x=alt.X("pct:Q", stack="normalize", title="% of those who answered",
                                    axis=alt.Axis(format="%")),
                            y=alt.Y("audience:N", title=None),
                            color=alt.Color("band:N", title="Score", sort=order,
                                            scale=alt.Scale(domain=order,
                                                            range=["#cde2fb", "#86b6ef", "#3987e5", "#184f95"]),
                                            legend=alt.Legend(orient="top")),
                            order=alt.Order("band:N"),
                            tooltip=["audience", "band", alt.Tooltip("pct:Q", format=".1f", title="%")],
                        ).properties(height=alt.Step(40)))
                st.caption(f"'Likely' = {C.CALL_988_LIKELY_MIN_0_10}-10. Audiences with fewer than "
                           f"{C.MIN_N} answers are not shown.")
            with right:
                st.markdown("**Does knowing more go with being more likely to call?**")
                ig = tables["intent_gap"]
                if not ig.empty:
                    ig = ig.assign(item_label=ig["item"].map(lbl))
                    shown = ig[ig["pct_likely_988"].notna()]
                    show(grouped_hbar(shown, "pct_likely_988", "item_label", "knowledge",
                                      {"Does not agree (1-3)": ORANGE, "Agrees (4-5)": BLUE},
                                      title="% likely to call 988", domain=[0, 100], suffix="%",
                                      tooltip=["item_label", "knowledge", alt.Tooltip("pct_likely_988:Q", format=".1f"),
                                               "n"]))
                    rho = ig.drop_duplicates("item")[["item_label", "spearman_rho", "spearman_p"]]
                    st.caption("Correlation between each knowledge rating and the 988 score (Spearman's rho): "
                               + "; ".join(f"{r_.item_label}: {r_.spearman_rho:.2f} ({p_text(r_.spearman_p)})"
                                           for r_ in rho.itertuples() if not is_blank(r_.spearman_rho))
                               + ". Groups with fewer than 10 people are hidden.")
            st.markdown("**Who answered this question?**")
            sub = tables.get("subset_988", pd.DataFrame())
            if not sub.empty:
                st.dataframe(analyze.safe_table(sub), hide_index=True, width="stretch")
                st.caption("Compares people who answered the 988 question with everyone else (Mann-Whitney p). "
                           "If they differ, 988 results may not represent all participants.")

# ---- Audiences & communities -------------------------------------------------------------
METRICS = {"nps": ("Net Promoter Score", "n_recommend", "+.0f", [-100, 100]),
           "recommend_mean": ("Recommend: mean (0-10)", "n_recommend", ".1f", [0, 10]),
           "pct_likely_988": ("% likely to call 988", "n_988", ".0f", [0, 100]),
           "retro_change_mean": ("Avg. before → after change (points)", "n_retro", ".2f", None)}
for col in res.likert_cols:
    METRICS[f"pct_agree_{col}"] = (f"% agree: {lbl(col)}", f"n_agree_{col}", ".0f", [0, 100])

with tabs[3]:
    intro("Audiences & communities")
    g1, g2, g3 = st.columns([1, 2, 1])
    # Options are display labels mapped back to keys (no format_func: works on every Streamlit version)
    GROUP_LABELS = {"Audience (students vs adults)": "audience", "County": "county", "Role": "role",
                    "Survey language": "language"}
    group = GROUP_LABELS[g1.selectbox("Compare by", list(GROUP_LABELS))]
    metric_by_label = {v[0]: k for k, v in METRICS.items()}
    metric = metric_by_label[g2.selectbox("Measure", list(metric_by_label))]
    can_split = group in ("county", "language")
    split = g3.toggle("Split by audience", value=False, disabled=not can_split,
                      help="Shows students and adults separately inside each group. Useful because "
                           "groups differ a lot in their share of students.") if can_split else False
    name, n_col, fmt, dom = METRICS[metric]
    tbl = analyze.by_group(res, group, df, split="audience" if split else None)
    if tbl.empty or metric not in tbl:
        st.info("This grouping isn't available in the current data.")
    else:
        vis = tbl[~tbl["suppressed"] & tbl[metric].notna()]
        if group == "audience":
            vis = vis[vis["group"] != NOT_REPORTED]
        if vis.empty:
            st.info(f"No group has at least {C.MIN_N} people who answered this question.")
        elif split:
            vis = vis[vis["split"].isin(AUDIENCE_COLORS)]
            show(grouped_hbar(vis, metric, "group", "split", AUDIENCE_COLORS, title=name, domain=dom, fmt=fmt,
                              tooltip=["group", "split", alt.Tooltip(f"{metric}:Q", format=fmt, title=name),
                                       alt.Tooltip(f"{n_col}:Q", title="n answered")]))
        else:
            vis = vis.assign(group=[f"{g} (n={int(n):,}{', thin' if n < C.THIN_N else ''})"
                                    for g, n in zip(vis["group"], vis[n_col])])
            show(hbar(vis, metric, "group", title=name, domain=dom, fmt=fmt,
                      color_map={f"{k} (n={int(n):,}{', thin' if n < C.THIN_N else ''})": AUDIENCE_COLORS[k]
                                 for k, n in zip(tbl["group"], tbl[n_col]) if k in AUDIENCE_COLORS and n == n}
                      if group == "audience" else None,
                      tooltip=["group", alt.Tooltip(f"{metric}:Q", format=fmt, title=name),
                               alt.Tooltip(f"{n_col}:Q", title="n answered"), alt.Tooltip("n:Q", title="n in group")]))
        hidden = len(tbl) - len(vis)
        if split and not vis.empty:
            thin_cells = vis[vis[n_col] < C.THIN_N]
            if len(thin_cells):
                st.caption("Thin (fewer than " + str(C.THIN_N) + " answered, indicative only): " + ", ".join(
                    f"{r_.group} · {r_.split} (n={int(r_[n_col])})" for _, r_ in thin_cells.iterrows()) + ".")
        if hidden:
            st.caption(f"{hidden} group(s) not shown: fewer than {C.MIN_N} people in the group, or "
                       f"fewer than {C.MIN_N} answered this question.")
        if group == "role":
            st.caption("People who chose several roles count in each.")
        tests = analyze.group_tests(res, group, df)
        if not tests.empty:
            st.markdown("**Are these differences bigger than chance?**")
            tt = tests[["metric", "groups_compared", "n", "test", "p_value", "effect", "verdict"]].copy()
            tt["p_value"] = tt["p_value"].map(p_text)
            st.dataframe(tt.rename(columns={"metric": "Measure", "groups_compared": "Groups compared",
                                            "test": "Test", "p_value": "p", "effect": "Effect size",
                                            "verdict": "Plain-language verdict"}),
                         hide_index=True, width="stretch")
            st.caption("Rank-based tests (Mann-Whitney for 2 groups, Kruskal-Wallis for 3+). Effect size tells "
                       "you whether a real difference is also a *meaningful* one. Differences describe, they "
                       "don't explain: groups also differ in who attends (see 'Split by audience').")
        with st.expander("Full table"):
            st.dataframe(analyze.safe_table(tbl), hide_index=True, width="stretch")

# ---- Trends & sessions --------------------------------------------------------------------
TREND_METRICS = {"nps": ("Net Promoter Score", [-100, 100]),
                 "pct_agree_after": ("% agree after (knowledge items)", [0, 100]),
                 "retro_change_mean": ("Avg. before → after change (points)", None),
                 "pct_delivery": ("% agree: delivery (presenter / organization)", [0, 100]),
                 "pct_likely_988": ("% likely to call 988", [0, 100]),
                 "recommend_mean": ("Recommend: mean (0-10)", [0, 10])}
with tabs[4]:
    intro("Trends & sessions")
    t1, t2 = st.columns([1, 2])
    period = t1.radio("Period", ["Quarter", "Month"], horizontal=True)
    trend_by_label = {v[0]: k for k, v in TREND_METRICS.items()}
    tmetric = trend_by_label[t2.selectbox("Measure", list(trend_by_label), key="trend_measure")]
    pcode = "Q" if period == "Quarter" else "M"
    parts = []
    overall_tr = analyze.trend(res, df, period=pcode)
    if not overall_tr.empty:
        parts.append(overall_tr.assign(audience="All"))
    by_aud = analyze.trend(res, df, period=pcode, by="audience")
    if not by_aud.empty:
        parts.append(by_aud[by_aud["audience"].isin(AUDIENCE_COLORS)])
    tr = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if not tr.empty and tmetric in tr:
        tr = tr[~tr["suppressed"] & tr[tmetric].notna()]
    if tr.empty or tmetric not in tr:
        st.info("Not enough dated responses for a trend.")
    else:
        show(lines(tr, "period", tmetric, "audience", {"All": "#52514e", **AUDIENCE_COLORS},
                   title=TREND_METRICS[tmetric][0], domain=TREND_METRICS[tmetric][1],
                   tooltip=["period", "audience", alt.Tooltip(f"{tmetric}:Q", format=".1f"), "n",
                            alt.Tooltip("pct_students:Q", format=".0f", title="% students")]))
        st.caption(f"Periods with fewer than {C.MIN_N} responses (per line) are not plotted. "
                   "When the 'All' line moves, check whether the audience mix changed too.")

    st.subheader("Session scorecard")
    ses = tables["sessions"]
    st.markdown(f"One row per training session (training date × county) with at least {C.MIN_N} responses. "
                f"A session is **flagged** if its Net Promoter Score is below {C.SESSION_ALERT_NPS_BELOW}, "
                f"knowledge agreement after training is below {C.SESSION_ALERT_AGREE_BELOW:.0f}%, or delivery "
                f"agreement is below {C.SESSION_ALERT_DELIVERY_BELOW:.0f}% (thresholds in `src/config.py`).")
    if ses.empty:
        st.info(f"No session has {C.MIN_N}+ responses in this view.")
    else:
        only = st.toggle("Show only flagged sessions", value=False)
        v = ses[ses["needs_follow_up"]] if only else ses
        cols = ["date", "county", "n", "thin", "pct_students", "nps", "pct_agree_after",
                "retro_change_mean", "pct_delivery", "n_988", "pct_likely_988", "flags"]
        view = analyze.safe_table(v)[cols].reset_index(drop=True)
        flagged = v["needs_follow_up"].to_numpy()
        # Tint flagged rows; a translucent orange reads on both light and dark backgrounds.
        styled = view.style.apply(
            lambda row: ["background-color: rgba(235, 104, 52, 0.18)" if flagged[row.name] else ""] * len(row),
            axis=1)
        st.dataframe(
            styled,
            hide_index=True, width="stretch",
            column_config={
                "date": st.column_config.DateColumn("Date", format="MMM D, YYYY"),
                "county": "County", "n": "Responses",
                "thin": st.column_config.CheckboxColumn(
                    "Thin", help=f"Fewer than {C.THIN_N} responses: a flag may just be chance. "
                                 "Look for a pattern across sessions before acting."),
                "pct_students": st.column_config.NumberColumn("% students", format="%.0f%%"),
                "nps": st.column_config.NumberColumn("NPS", format="%+.0f"),
                "pct_agree_after": st.column_config.NumberColumn("% agree after", format="%.0f%%"),
                "retro_change_mean": st.column_config.NumberColumn("Change (pts)", format="%+.2f"),
                "pct_delivery": st.column_config.NumberColumn("Delivery % agree", format="%.0f%%"),
                "n_988": "n (988 Q)",
                "pct_likely_988": st.column_config.NumberColumn("% likely 988", format="%.0f%%"),
                "flags": "Follow-up flags"})
        a = ses.attrs
        n_flag = int(ses["needs_follow_up"].sum())
        n_flag_thin = int((ses["needs_follow_up"] & ses["thin"]).sum())
        st.caption(f"{n_flag} of {len(ses)} sessions flagged (shown first, shaded)"
                   + (f", {n_flag_thin} of them thin (under {C.THIN_N} responses)" if n_flag_thin else "") + ". "
                   f"{a.get('hidden_sessions', 0)} smaller sessions ({a.get('hidden_responses', 0)} responses) "
                   f"are not listed individually but are included in every other view. "
                   "Use flags as a prompt to talk with the facilitator, not as a verdict.")

# ---- Participant voice --------------------------------------------------------------------
with tabs[5]:
    intro("Participant voice")
    st.caption("Themes in the two open-ended questions, coded with transparent keyword rules "
                "(`src/text_themes.py`). One answer can mention several themes. Individual answers are "
                "never shown, to protect participants.")
    vsplit = st.toggle("Compare students and adults", value=False, key="v_split")
    for col in res.text_cols:
        st.subheader(res.label(col))
        th = themes.get(col)
        if th is None or th.empty or int(th["n_answered"].iloc[0]) < C.MIN_N:
            st.info(f"Fewer than {C.MIN_N} people in this view answered this question.")
            continue
        if vsplit:
            tb = themes.get(f"{col}_by_audience", pd.DataFrame())
            tb = tb[tb["group"].isin(AUDIENCE_COLORS) & tb["pct_of_answered"].notna()] if not tb.empty else tb
            if tb.empty:
                st.info("Not enough answers to split by audience.")
                continue
            order = th["theme"].tolist()
            show(grouped_hbar(tb, "pct_of_answered", "theme", "group", AUDIENCE_COLORS, sort=order,
                              title="% of people who answered", suffix="%",
                              tooltip=["theme", "group", "count", alt.Tooltip("pct_of_answered:Q", format=".1f")]))
        else:
            shown = th[~th["under_min_n"]]
            show(hbar(shown, "pct_of_answered", "theme", title="% of people who answered", suffix="%",
                      sort=shown["theme"].tolist(),
                      tooltip=["theme", "count", alt.Tooltip("pct_of_answered:Q", format=".1f")]))
        n_hidden = int(th["under_min_n"].sum())
        st.caption(f"{int(th['n_answered'].iloc[0]):,} people answered."
                   + (f" {n_hidden} theme(s) with fewer than {C.MIN_N} mentions not shown." if n_hidden else ""))
    with st.expander("How are themes assigned? (keyword rules)"):
        for col in res.text_cols:
            st.markdown(f"**{res.label(col)}**")
            for theme, pats in text_themes.THEMES_BY_COLUMN.get(col, text_themes.ALL_THEMES).items():
                st.markdown(f"- *{theme}*: `" + "`, `".join(pats[:6]) + ("`, …" if len(pats) > 6 else "`"))
        st.caption("Patterns are regular expressions. To add a theme or keyword, edit src/text_themes.py and "
                   "check accuracy with scripts/validate_themes.py (see README).")

# ---- Data quality & methods ------------------------------------------------------------
with tabs[6]:
    intro("Data quality & methods")
    st.markdown("**Data-quality checks** for the current view")
    st.dataframe(tables["quality"], hide_index=True, width="stretch")
    sens = tables.get("sensitivity", pd.DataFrame())
    if not sens.empty:
        st.markdown("**Robustness:** do the before → after results hold without people who gave the same "
                    "answer to every question?")
        s2 = analyze.safe_table(sens).assign(item=sens["item"].map(lbl))
        st.dataframe(s2[["sample", "item", "n", "top_box_before", "top_box_after", "change"]].rename(
            columns={"sample": "Sample", "item": "Item", "top_box_before": "% agree before",
                     "top_box_after": "% agree after", "change": "Mean change"}), hide_index=True, width="stretch")
    with st.expander("How the file was read (column detection and cleaning report)"):
        st.code("\n".join(res.report), language=None)
    methods = ROOT / "docs" / "METHODS.md"
    if methods.exists():
        with st.expander("Methods and definitions"):
            st.markdown(methods.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Download: aggregate tables only (never row-level data or open text)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False, max_entries=50)
def build_download(key_data: tuple, key_filters: tuple, filters: str, n_view: int, n_all: int,
                   _tables: dict, _themes: dict) -> bytes:
    """Cached per data file + filters, so it isn't rebuilt on every click."""
    created = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    about = pd.DataFrame({"item": ["Filters", "Responses in this download", "Responses in the file",
                                   "Created", "Privacy"],
                          "value": [filters, f"{n_view:,}", f"{n_all:,}", created,
                                    f"Counts below {C.MIN_N} shown as '{SMALL}'; no individual responses"]})
    safe = {"about": about,
            **analyze.safe_tables({**_tables, **{f"themes_{k}": v for k, v in _themes.items()}})}
    xlsx = io.BytesIO()
    analyze.write_excel(safe, xlsx)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("summary_report.xlsx", xlsx.getvalue())
        for name, t in safe.items():
            z.writestr(f"csv/{name}.csv", t.to_csv(index=False))
        z.writestr("README.txt",
                   "Aggregate tables from the 988 Training Insights dashboard.\n\n"
                   f"Filters: {filters}\n"
                   f"Responses in this download: {n_view:,} of {n_all:,}\n"
                   f"Created: {created}\n\n"
                   f"Counts below {C.MIN_N} are shown as '{SMALL}' and those groups' results are blank. "
                   "No individual responses are included.\n"
                   "Definitions: docs/METHODS.md in the project folder.\n")
    return buf.getvalue()


st.sidebar.download_button(
    "Download summary (Excel + CSV)",
    data=build_download(data_key, filter_key, filters_text, len(df), len(df_all), tables, themes),
    file_name="988_training_summary.zip", mime="application/zip",
    help=f"Aggregate tables for the current filters. Counts under {C.MIN_N} are hidden. "
         "No individual responses are included. Good for grant reports.")
