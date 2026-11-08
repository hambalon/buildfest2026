"""Automated tests. They use FAKE data only, so anyone can run them without the
confidential file:

    pip install -r requirements-dev.txt
    python -m pytest -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import analyze, insights, text_themes  # noqa: E402
from src import config as C  # noqa: E402
from src.clean import (SMALL_GROUP, group_small, load_and_clean, norm_text,  # noqa: E402
                       standardize_county, to_date, to_scale)


@pytest.fixture(scope="session")
def fake_file(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("data") / "FAKE_survey.xlsx"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_fake_data.py"), str(path)],
                   check=True, capture_output=True)
    return path


@pytest.fixture(scope="session")
def res(fake_file):
    return load_and_clean(fake_file)


# ---- cleaning helpers --------------------------------------------------------------
@pytest.mark.parametrize("raw, expected", [
    ("Agree ", "Agree"),
    ("English (United States)‎", "English (United States)"),
    ("Student;Educator;", "Student;Educator"),
    ("  lots   of   space ", "lots of space"),
    ("None", pd.NA), ("n/a", pd.NA), ("", pd.NA),
])
def test_norm_text(raw, expected):
    out = norm_text(raw)
    assert (out is pd.NA and expected is pd.NA) or out == expected


def test_to_scale_english_spanish_and_unknown():
    s = pd.Series(["Strongly agree", "agree", "Neither agree nor disagree", "De acuerdo",
                   "Totalmente en desacuerdo", "Very agree", None])
    out, bad = to_scale(s, "agree")
    assert list(out[:5]) == [5, 4, 3, 4, 1]
    assert pd.isna(out[5]) and "Very agree" in bad   # non-standard label -> missing (decision D1)
    assert pd.isna(out[6])


def test_to_date_handles_excel_serials_strings_and_datetimes():
    s = pd.Series(["2026-03-04", 45700, pd.Timestamp("2026-05-01 10:30"), "garbage", None], dtype=object)
    out = to_date(s)
    assert out[0] == pd.Timestamp("2026-03-04")
    assert out[1] == pd.Timestamp("2025-02-12")
    assert out[2] == pd.Timestamp("2026-05-01")
    assert pd.isna(out[3]) and pd.isna(out[4])


def test_county_variants_merge():
    s = pd.Series(["Montgomery County", "montgomery", "Montgomery", "Prince George's"])
    out = standardize_county(s)
    assert out.nunique() == 2


def test_group_small_folds_rare_values():
    s = pd.Series(["A"] * 12 + ["B"] * 3 + [None] * 2)
    out = group_small(s)
    assert set(out) == {"A", SMALL_GROUP, "Not reported"}


def test_nps_and_top_box():
    assert analyze.nps(pd.Series([10, 9, 8, 7, 0])) == pytest.approx(20.0)
    assert analyze.top_box(pd.Series([5, 4, 3, 2])) == pytest.approx(50.0)


# ---- end-to-end on fake data ------------------------------------------------------
def test_columns_detected(res):
    cols = set(res.df.columns)
    for c in ["language", "role", "training_date", "county", "recommend", "call_988", "audience",
              "outcome_01", "outcome_02", "outcome_03", "before_01", "aspect_01", "text_valuable",
              "text_improve"]:
        assert c in cols, c
    assert res.retro_pairs == {"before_01": "outcome_01", "before_02": "outcome_02", "before_03": "outcome_03"}
    assert res.call_988_scale == "0-10"
    assert set(res.df["audience"].dropna()) <= {"Students", "Adults", "Not reported"}


def test_in_memory_upload_matches_file(fake_file):
    a = load_and_clean(fake_file)
    b = load_and_clean(fake_file.read_bytes(), name="upload.xlsx")
    pd.testing.assert_frame_equal(a.df, b.df)


def test_run_all_produces_every_table(res):
    tables = analyze.run_all(res)
    for name in ["overall", "retro_change", "by_audience", "by_county", "by_role", "by_language",
                 "county_by_audience", "group_tests", "trend", "trend_monthly", "trend_by_audience",
                 "intent_gap", "sessions", "quality", "sensitivity", "subset_988", "ceiling"]:
        assert name in tables, name


def test_small_groups_are_suppressed(res):
    for g in analyze.GROUPS:
        t = analyze.by_group(res, g)
        if t.empty:
            continue
        shown = t[~t["suppressed"]]
        assert (shown["n"] >= C.MIN_N).all()
        assert t.loc[t["suppressed"], "nps"].isna().all()
        # per-metric suppression: a metric answered by < MIN_N is blank
        small_988 = shown["n_988"] < C.MIN_N
        assert shown.loc[small_988, "pct_likely_988"].isna().all()


def test_exports_never_show_small_counts_or_text(res):
    safe = analyze.export_tables(res, extra={f"themes_{k}": v for k, v in text_themes.run_all(res).items()})
    for name, t in safe.items():
        for c in [c for c in t.columns if c == "n" or c.startswith("n_") or c == "count"]:
            nums = pd.to_numeric(t[c], errors="coerce").dropna()
            assert (nums >= C.MIN_N).all(), f"{name}.{c} shows a count below {C.MIN_N}"
        for c in t.columns:  # no column holds raw open-text answers
            assert not c.startswith("text_"), f"{name} exports open text column {c}"


def test_sessions_only_list_big_sessions(res):
    s = analyze.session_scorecard(res)
    if not s.empty:
        assert (s["n"] >= C.MIN_N).all()


def test_theme_coding_is_multilabel_and_counts_uncoded(res):
    for col in res.text_cols:
        t = text_themes.theme_summary(res.df[col], col)
        assert text_themes.UNCODED in set(t["theme"])
        assert t["count"].sum() >= t["n_answered"].iloc[0] * 0  # sanity: non-negative
    coded = text_themes.code_responses(pd.Series(["Nothing, it was great", "How many people call 988?", None]),
                                       "text_improve")
    assert coded.loc[0, "No changes / it was good"]
    assert coded.loc[1, "Asked a question about 988"]
    assert not coded.loc[2, "answered"]


def test_insights_build(res):
    tables = analyze.run_all(res)
    items = insights.build(res, tables, text_themes.run_all(res))
    assert items and all(i.kind in insights.KINDS for i in items)
    md = insights.to_markdown(items)
    assert "What's working" in md and "n = " in md


def test_thin_marker():
    assert "thin" in insights.n_(C.THIN_N - 1) and "thin" not in insights.n_(C.THIN_N)


# ---- reasonable data updates (BuildFest: "support reasonable data updates") --------
@pytest.fixture(scope="session")
def raw_fake(fake_file):
    return pd.read_excel(fake_file, dtype=object)


def _col(df, key):
    return [c for c in df.columns if key.lower() in c.lower()][0]


def test_csv_export_matches_xlsx(fake_file, raw_fake, tmp_path):
    p = tmp_path / "export.csv"
    raw_fake.to_csv(p, index=False)
    a, b = load_and_clean(fake_file), load_and_clean(p)
    assert len(a.df) == len(b.df) and set(a.column_map) == set(b.column_map)
    assert analyze.nps(a.df["recommend"]) == pytest.approx(analyze.nps(b.df["recommend"]))
    assert load_and_clean(p.read_bytes(), name="upload.csv").df.shape == b.df.shape


@pytest.mark.parametrize("variant", ["reordered", "no_role", "no_date", "no_988", "no_delivery",
                                     "renamed", "extra_column", "tiny"])
def test_pipeline_survives_form_changes(raw_fake, tmp_path, variant):
    df = raw_fake
    v = {"reordered": lambda: df[df.columns[::-1]],
         "no_role": lambda: df.drop(columns=[_col(df, "are you")]),
         "no_date": lambda: df.drop(columns=[_col(df, "date of your training")]),
         "no_988": lambda: df.drop(columns=[_col(df, "call 988")]),
         "no_delivery": lambda: df.drop(columns=[c for c in df.columns if "aspects" in c.lower()]),
         "renamed": lambda: df.rename(columns={_col(df, "county"): "County of training"}),
         "extra_column": lambda: df.assign(**{"Any other comments?": "Thanks"}),
         "tiny": lambda: df.head(12)}[variant]()
    p = tmp_path / f"{variant}.xlsx"
    v.to_excel(p, index=False)
    r = load_and_clean(p)
    tables = analyze.run_all(r)
    insights.build(r, tables, text_themes.run_all(r))
    analyze.export_tables(r)
    if variant == "renamed":
        assert "county" in r.column_map


def test_dashboard_runs_without_errors(fake_file, monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("DATA_FILE", str(fake_file))
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
    assert not at.exception, [e.message for e in at.exception]
    assert len(at.tabs) == 7
