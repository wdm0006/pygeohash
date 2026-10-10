"""Value checks for the benchmark page generator, driven by hand-built report fixtures.

No benchmark is run: each fixture mimics the pytest-benchmark JSON the generator
reads, with round numbers so batch normalization and mode/size attribution can
be asserted exactly.
"""

import importlib.util
import json
import os
import sys

import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_comparison_benchmark.py")
spec = importlib.util.spec_from_file_location("run_comparison_benchmark", SCRIPT)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def entry(group, library, mode, size, median_ns):
    return {
        "name": f"test_{group.split('-batch')[0]}_batch[{library}@{mode}-n{size}]",
        "group": group,
        "extra_info": {"library": library, "mode": mode, "size": size, "precision": 9},
        "stats": {"median": median_ns / 1e9},
    }


def scalar(group, library, median_ns):
    return {"name": f"test_{group}[{library}]", "group": group, "stats": {"median": median_ns / 1e9}}


def report(scale=1.0):
    """One run: pygeohash bulk beats its own loop at 10k but loses to geohashr's loop at 100."""
    return {
        "datetime": "2026-10-10T00:00:00",
        "machine_info": {"cpu": {"brand_raw": "Test CPU", "count": 4}, "machine": "arm64"},
        "benchmarks": [
            entry("encode-batch-100", "pygeohash", "bulk", 100, 10_000 * scale),
            entry("encode-batch-100", "pygeohash", "scalar-loop", 100, 30_000 * scale),
            entry("encode-batch-100", "geohashr", "scalar-loop", 100, 8_000 * scale),
            entry("encode-batch-10000", "pygeohash", "bulk", 10_000, 2_000_000 * scale),
            entry("encode-batch-10000", "pygeohash", "scalar-loop", 10_000, 3_000_000 * scale),
            entry("decode-batch-100", "pygeohash", "bulk", 100, 20_000 * scale),
            entry("decode-batch-100", "pygeohash", "scalar-loop", 100, 25_000 * scale),
            entry("decode-batch-10000", "pygeohash", "bulk", 10_000, 4_000_000 * scale),
            entry("decode-batch-10000", "pygeohash", "scalar-loop", 10_000, 5_000_000 * scale),
            scalar("encode", "pygeohash", 200.0 * scale),
        ],
    }


REPORTS = [report(1.0), report(1.1), report(0.9)]


def rows_by_key(group):
    return {(r["library"], r["mode"]): r for r in generator.collect_batch_rows(REPORTS, group)}


def test_per_item_time_divides_batch_time_by_its_own_batch_size():
    small = rows_by_key("encode-batch-100")[("pygeohash", "bulk")]
    large = rows_by_key("encode-batch-10000")[("pygeohash", "bulk")]
    assert small["median_ns"] == pytest.approx(10_000)
    assert small["per_item_ns"] == pytest.approx(100.0)  # 10,000 ns / 100 records
    assert large["median_ns"] == pytest.approx(2_000_000)
    assert large["per_item_ns"] == pytest.approx(200.0)  # 2,000,000 ns / 10,000 records
    assert (small["per_item_low_ns"], small["per_item_high_ns"]) == pytest.approx((90.0, 110.0))
    assert (small["low_ns"], small["high_ns"]) == pytest.approx((9_000, 11_000))


def test_modes_and_sizes_are_attributed_separately():
    rows = rows_by_key("encode-batch-100")
    assert set(rows) == {("pygeohash", "bulk"), ("pygeohash", "scalar-loop"), ("geohashr", "scalar-loop")}
    assert rows[("pygeohash", "scalar-loop")]["median_ns"] == pytest.approx(30_000)
    assert {r["size"] for r in rows.values()} == {100}
    assert {r["size"] for r in rows_by_key("decode-batch-10000").values()} == {10_000}
    assert rows[("pygeohash", "bulk")]["ratio"] == pytest.approx(1.0)
    assert rows[("geohashr", "scalar-loop")]["ratio"] == pytest.approx(0.8)  # faster than pygeohash bulk


def test_rows_sort_by_batch_time_and_report_the_loser():
    rows = generator.collect_batch_rows(REPORTS, "encode-batch-100")
    assert [(r["library"], r["mode"]) for r in rows] == [
        ("geohashr", "scalar-loop"),
        ("pygeohash", "bulk"),
        ("pygeohash", "scalar-loop"),
    ]
    summary = " ".join(generator.batch_summary(rows).split())
    assert "0.33x" in summary  # bulk 10 us vs its loop 30 us
    assert "``geohashr`` (scalar loop)" in summary  # a row where pygeohash loses is named


def test_scalar_groups_ignore_batch_entries():
    scalar_rows = generator.collect_rows(REPORTS, "encode")
    assert [r["library"] for r in scalar_rows] == ["pygeohash"]
    assert scalar_rows[0]["median_ns"] == pytest.approx(200.0)
    assert generator.library_name(REPORTS[0]["benchmarks"][0]) == "pygeohash"
    assert {row["group"] for row in generator.stability_rows(REPORTS)} == {"encode"}  # batch groups excluded


def test_page_labels_each_size_and_mode_and_retains_scalar_groups():
    page = generator.render_page(REPORTS)
    for heading in ("Encode, 100 records", "Encode, 10,000 records", "Decode, 100 records", "Decode, 10,000 records"):
        assert heading in page
    assert "native bulk call" in page and "scalar loop" in page
    assert "Batch time (us), range over 3 runs" in page and "Time per item (ns)" in page
    assert "\nEncode\n------" in page  # the scalar encode group is still rendered
    assert "10.0 (9.0 - 11.0)" in page  # 10,000 ns bulk batch in us, with its range
    assert "100.0 (90.0 - 110.0)" in page  # per item ns


def test_saved_report_replay_matches_without_running_the_suite(tmp_path, monkeypatch):
    paths = []
    for index, data in enumerate(REPORTS):
        path = tmp_path / f"run{index}.json"
        path.write_text(json.dumps(data))
        paths.append(str(path))

    def refuse(*args, **kwargs):
        raise AssertionError("replay must not run the benchmark suite")

    monkeypatch.setattr(generator, "run_benchmarks", refuse)
    output = tmp_path / "page.rst"
    argv = ["run_comparison_benchmark.py", "--output", str(output)]
    for path in paths:
        argv += ["--report", path]
    monkeypatch.setattr(sys, "argv", argv)
    generator.main()

    replayed = output.read_text()
    assert replayed == generator.render_page(json.loads(json.dumps(REPORTS)))
    assert "Encode, 100 records" in replayed and "100.0 (90.0 - 110.0)" in replayed


def test_readme_batch_table_uses_the_same_rows():
    table = generator.render_markdown_batch_summary(REPORTS)
    assert "**Encode, 100 records** (precision 9)" in table
    assert "| **pygeohash** | native bulk call | 10.0 (9.0-11.0) | 100.0 | 1.00x |" in table
    assert "| geohashr | scalar loop | 8.0 (7.2-8.8) | 80.0 | 0.80x |" in table
