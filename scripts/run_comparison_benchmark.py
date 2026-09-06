#!/usr/bin/env python
"""Run the cross-library benchmark suite and generate the documentation page.

This script drives ``tests/test_benchmark_comparison.py`` with pytest-benchmark,
reads the resulting JSON report, and writes a reStructuredText page containing
one table per benchmark group plus a provenance block describing the machine the
numbers came from.

Usage:
    python scripts/run_comparison_benchmark.py
    python scripts/run_comparison_benchmark.py --output docs/source/benchmarks.rst

The ``benchmark`` extra must be installed for the competing libraries to appear:

    uv pip install -e ".[dev,benchmark]"

Every timed pass is preceded by a discarded warmup pass of the full suite, so
first-touch cost does not leak into the published medians (skip with
``--no-warmup``).
"""

import argparse
import importlib.metadata
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import textwrap

# Add the parent directory to the path so we can import pygeohash
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BENCHMARK_TEST = os.path.join("tests", "test_benchmark_comparison.py")
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "docs", "source", "benchmarks.rst")

# The suite is cheap, so repeat it and publish the spread rather than one draw.
DEFAULT_REPEATS = 3

# Group order and headings for the generated page.
GROUPS = [
    ("encode", "Encode", "Encode ``(42.6, -5.6)`` to a precision-9 geohash."),
    ("decode", "Decode", "Decode ``ezs42e44y`` back to coordinates."),
    ("bbox", "Bounding box", "Look up the bounding box of the ``ezs42e44y`` cell."),
    ("validate", "Validation", 'Check ``is_valid_geohash("ezs42e44y")``.'),
    ("adjacent", "Adjacent", "Step one cell north of ``ezs42e44y``."),
    ("adjacent-border", "Adjacent (border)", "Step west of ``u00000``, across the antimeridian."),
    ("box-small", "Box enumeration (small)", "Enumerate ``geohashes_in_box`` over a 4-cell box at precision 9."),
    ("box-large", "Box enumeration (large)", "Enumerate ``geohashes_in_box`` over a 361-cell box at precision 6."),
]

# Implementation of each measured library, mirroring the table in the test module.
IMPLEMENTATIONS = {
    "pygeohash": "C extension",
    "python-geohash": "C++ extension",
    "geohashr": "Rust extension",
    "pygeohash-fast": "Rust extension",
    "libgeohash": "pure Python",
    "geolib": "pure Python",
    "geohash-tools": "pure Python",
}

# Implementation classes whose sub-microsecond medians are tracked for
# run-to-run stability in the generated page.
EXTENSION_LABELS = {"C extension", "C++ extension", "Rust extension"}

# The published stability expectation: after warmup, a compiled library's
# per-run medians stay within this relative spread.
STABILITY_SPREAD_LIMIT = 0.20

REPRODUCE_COMMAND = 'uv pip install -e ".[dev,benchmark]"\npython scripts/run_comparison_benchmark.py'


def run_benchmarks(json_paths, warmup_passes=1):
    """Run the comparison suite once per path, writing a JSON report each time.

    ``warmup_passes`` discarded suite runs happen before the timed ones: a
    library's first-touch cost used to land in the first run's medians and from
    there in the median-of-medians the page publishes. The suite is then
    repeated so the page can report how much each figure moved between runs
    rather than publishing a single draw from a noisy process.
    """
    passes = []
    for _ in range(max(0, warmup_passes)):
        handle, path = tempfile.mkstemp(suffix=".json", prefix="pygeohash-benchmark-warmup-")
        os.close(handle)
        passes.append((path, False))
    passes.extend((path, True) for path in json_paths)

    total = len(passes)
    for index, (json_path, keep) in enumerate(passes, start=1):
        label = f"{index} of {total}" + ("" if keep else " (warmup, discarded)")
        print(f"Running the comparison benchmark suite ({label})...")
        command = [
            sys.executable,
            "-m",
            "pytest",
            BENCHMARK_TEST,
            "--benchmark-enable",
            "--benchmark-group-by=group",
            f"--benchmark-json={json_path}",
            "--no-cov",
        ]
        # pyproject's pytest addopts already carry -v; the JSON report is parsed
        # instead of the terminal tables, so stdout is only progress information.
        subprocess.run(command, cwd=REPO_ROOT, check=True)  # noqa: S603
        if not keep:
            os.remove(json_path)


def library_name(benchmark):
    """Extract the measured library from a benchmark's test id.

    The ``params`` entry serializes as the repr of the ``Adapter`` dataclass
    (including lambda addresses), so the name is taken from ``name`` instead:
    ``test_encode[geohashr]`` -> ``geohashr``.
    """
    name = benchmark["name"]
    start = name.index("[") + 1
    return name[start : name.rindex("]")]


def collect_rows(reports, group):
    """Return one row per library in a group, sorted by median time.

    Each row carries the median of the per-run medians plus the lowest and
    highest median observed, so the table can show how far a figure moved.
    """
    per_library = {}
    for report in reports:
        for benchmark in report["benchmarks"]:
            if benchmark["group"] != group:
                continue
            median_ns = benchmark["stats"]["median"] * 1e9
            per_library.setdefault(library_name(benchmark), []).append(median_ns)

    rows = []
    for library, medians in per_library.items():
        median_ns = statistics.median(medians)
        rows.append(
            {
                "library": library,
                "median_ns": median_ns,
                "ops": 1e9 / median_ns,
                "low_ns": min(medians),
                "high_ns": max(medians),
            }
        )
    rows.sort(key=lambda row: row["median_ns"])

    baseline = next((row["median_ns"] for row in rows if row["library"] == "pygeohash"), None)
    for row in rows:
        row["ratio"] = row["median_ns"] / baseline if baseline else None
    return rows


def stability_rows(reports):
    """Per-run medians for the compiled libraries, for the stability table.

    Sub-microsecond medians are the ones cold-start contamination used to move
    between repeats, so that is what the stability table tracks. Returns one
    row per (group, library) with each timed run's median and the largest
    relative gap between any two runs.
    """
    per_key = {}
    for run_index, report in enumerate(reports):
        for benchmark in report["benchmarks"]:
            key = (benchmark["group"], library_name(benchmark))
            per_key.setdefault(key, {})[run_index] = benchmark["stats"]["median"] * 1e9

    rows = []
    for (group, library), medians in per_key.items():
        if IMPLEMENTATIONS.get(library) not in EXTENSION_LABELS:
            continue
        values = [medians[run] for run in sorted(medians)]
        middle = statistics.median(values)
        spread = (max(values) - min(values)) / middle if middle else 0.0
        rows.append({"group": group, "library": library, "medians": values, "spread": spread})
    rows.sort(key=lambda row: (row["group"], row["library"]))
    return rows


def format_table(rows, repeats):
    """Render one group's rows as a reStructuredText list-table."""
    lines = [
        ".. list-table::",
        "   :header-rows: 1",
        "   :widths: 22 18 14 20 14 12",
        "",
        "   * - Library",
        "     - Implementation",
        "     - Median (ns)",
        f"     - Range over {repeats} runs (ns)",
        "     - Ops/sec",
        "     - vs pygeohash",
    ]
    for row in rows:
        library = row["library"]
        label = f"**{library}**" if library == "pygeohash" else library
        ratio = f"{row['ratio']:.2f}x" if row["ratio"] is not None else "n/a"
        lines.extend(
            [
                f"   * - {label}",
                f"     - {IMPLEMENTATIONS.get(library, 'unknown')}",
                f"     - {row['median_ns']:,.0f}",
                f"     - {row['low_ns']:,.0f} - {row['high_ns']:,.0f}",
                f"     - {row['ops']:,.0f}",
                f"     - {ratio}",
            ]
        )
    return "\n".join(lines)


def format_stability(rows, repeats):
    """Render the run-to-run stability section, or an empty string if unused."""
    if not rows:
        return ""

    lines = [
        "Stability",
        "---------",
        "",
        "Each compiled library's median on every timed run, after the warmup pass, with",
        "the largest relative gap between any two runs. Cold-start contamination used to",
        "move these figures between repeats before the suite warmed up; a spread within",
        f"{STABILITY_SPREAD_LIMIT:.0%} is the expected steady state.",
        "",
        ".. list-table::",
        "   :header-rows: 1",
        f"   :widths: 18 22 {9 * repeats} 10",
        "",
        "   * - Group",
        "     - Library",
    ]
    lines.extend(f"     - Run {run + 1} (ns)" for run in range(repeats))
    lines.extend(["     - Spread", ""])

    over_limit = []
    for row in rows:
        flag = " (!)" if row["spread"] > STABILITY_SPREAD_LIMIT else ""
        if flag:
            over_limit.append(row)
        lines.append(f"   * - {row['group']}")
        lines.append(f"     - {row['library']}")
        lines.extend(f"     - {median:,.0f}" for median in row["medians"])
        lines.append(f"     - {row['spread']:.1%}{flag}")

    if over_limit:
        names = ", ".join(f"``{row['library']}`` ({row['group']})" for row in over_limit)
        lines.extend(
            [
                "",
                textwrap.fill(
                    f"The spread of {names} exceeded {STABILITY_SPREAD_LIMIT:.0%} on this run; "
                    "treat those figures with suspicion and rerun before quoting them.",
                    width=88,
                    break_on_hyphens=False,
                    break_long_words=False,
                ),
            ]
        )
    return "\n".join(lines)


def noise_note(rows):
    """Describe any adjacent pair the repeated runs did not separate.

    If the range of medians one library produced overlaps the next library's,
    the two were not told apart by this measurement and their relative order in
    the table carries no information.
    """
    pairs = []
    for faster, slower in zip(rows, rows[1:]):
        if slower["low_ns"] <= faster["high_ns"]:
            pairs.append(f"``{faster['library']}`` and ``{slower['library']}``")
    if not pairs:
        return ""
    joined = "; ".join(pairs)
    return textwrap.fill(
        f"The repeated runs did not separate {joined}. Their ranges of medians overlap, so "
        "their relative order in the table is within measurement noise and swaps between "
        "runs: read them as tied.",
        width=88,
        break_on_hyphens=False,
        break_long_words=False,
    )


def summary_sentences(rows):
    """Describe where pygeohash lands relative to the rest of a group."""
    by_library = {row["library"]: row for row in rows}
    pygeohash = by_library.get("pygeohash")
    if pygeohash is None:
        return ""

    clauses = []
    named = {"pygeohash"}
    baseline = by_library.get("python-geohash")
    if baseline is not None:
        named.add("python-geohash")
        ratio = pygeohash["median_ns"] / baseline["median_ns"]
        if ratio > 1:
            clauses.append(f"takes {ratio:.2f}x the median time of ``python-geohash``")
        else:
            clauses.append(f"is {1 / ratio:.2f}x faster than ``python-geohash``")

    pure_python = [row for row in rows if IMPLEMENTATIONS.get(row["library"]) == "pure Python"]
    if pure_python:
        fastest = min(pure_python, key=lambda row: row["median_ns"])
        ratio = fastest["median_ns"] / pygeohash["median_ns"]
        clauses.append(f"is {ratio:.1f}x faster than ``{fastest['library']}``, the quickest pure-Python entry")

    if not clauses:
        return ""

    sentence = "On this machine pygeohash " + " and ".join(clauses) + "."

    faster = [row for row in rows if row["median_ns"] < pygeohash["median_ns"] and row["library"] not in named]
    if faster:
        names = ", ".join(f"``{row['library']}``" for row in faster)
        verb = "is" if len(faster) == 1 else "are"
        sentence += f" {names} {verb} faster still."
    return textwrap.fill(sentence, width=88, break_on_hyphens=False, break_long_words=False)


def installed_versions(libraries):
    """Return the installed distribution version of every measured library."""
    versions = {}
    for library in libraries:
        try:
            versions[library] = importlib.metadata.version(library)
        except importlib.metadata.PackageNotFoundError:  # pragma: no cover - defensive
            versions[library] = "unknown"
    return versions


def format_provenance(reports, libraries):
    """Render the environment block describing where the numbers came from."""
    report = reports[0]
    machine = report["machine_info"]
    cpu = machine.get("cpu", {})
    run_date = report["datetime"].split("T")[0]

    lines = [
        f"* **Date of run**: {run_date} ({len(reports)} repeats of the suite, after a warmup pass)",
        f"* **Machine**: {cpu.get('brand_raw', 'unknown CPU')} "
        f"({machine.get('machine', platform.machine())}, {cpu.get('count', '?')} cores)",
        f"* **Operating system**: {machine.get('system', platform.system())} "
        f"{machine.get('release', platform.release())}",
        f"* **Python**: {machine.get('python_implementation', 'CPython')} "
        f"{machine.get('python_version', platform.python_version())}",
        f"* **pytest-benchmark**: {importlib.metadata.version('pytest-benchmark')}",
        "",
        "Installed versions of every library measured:",
        "",
    ]
    versions = installed_versions(libraries)
    for library in sorted(versions):
        lines.append(f"* ``{library}`` {versions[library]}")
    return "\n".join(lines)


def render_page(reports):
    """Build the whole reStructuredText page from the benchmark reports."""
    libraries = sorted({library_name(b) for report in reports for b in report["benchmarks"]})
    repeats = len(reports)

    parts = [
        "Benchmarks",
        "==========",
        "",
        "How does PyGeoHash compare to the other geohash libraries on PyPI? This page",
        "publishes the numbers rather than leaving the question open. It is generated by",
        "``scripts/run_comparison_benchmark.py`` from the suite in",
        "``tests/test_benchmark_comparison.py``, which measures every library on identical",
        "work.",
        "",
        "What is measured",
        "----------------",
        "",
        "Every library receives the same inputs: latitude ``42.6``, longitude ``-5.6`` and",
        "precision ``9`` for encoding, and the geohash ``ezs42e44y`` for decoding,",
        "bounding-box lookups, and adjacency. Every measured call asserts its result,",
        "decode and bounding-box lookups included, so the comparison is genuinely like",
        "for like.",
        "",
        "Adapters exist where a competitor's API allows one; where it does not, the",
        "library drops out of that operation's table. ``python-geohash`` has no",
        "single-neighbor lookup (``neighbors()`` computes all eight, which is not",
        "comparable work), no standalone validity check, and no box enumeration;",
        "``pygeohash-fast`` ships only encode and decode; ``geohash-tools`` offers no",
        "bounding box helper. No competitor exposes a standalone validity check or box",
        "enumeration, so those tables list pygeohash only. Two others are excluded from",
        "the suite entirely: ``geohash-hilbert`` computes a Hilbert-curve variant rather",
        "than a standard geohash, and ``mzgeohash`` takes no precision parameter, so",
        "equal work cannot be guaranteed.",
        "",
        f"The suite runs one discarded warmup pass and then {repeats} timed passes. Each",
        "library's headline figure is the median of its per-run medians, and the range",
        "column gives the lowest and highest median it produced, so the run-to-run",
        "movement behind every number is visible. Ops/sec is derived from the headline",
        "median, and the final column is each library's median divided by pygeohash's.",
        "",
    ]

    for group, heading, description in GROUPS:
        rows = collect_rows(reports, group)
        if not rows:
            continue
        parts.extend([heading, "-" * len(heading), "", description, ""])
        parts.append(format_table(rows, repeats))
        parts.append("")
        summary = summary_sentences(rows)
        if summary:
            parts.extend([summary, ""])
        note = noise_note(rows)
        if note:
            parts.extend([note, ""])

    stability = format_stability(stability_rows(reports), repeats)
    if stability:
        parts.extend([stability, ""])

    parts.extend(
        [
            "Environment",
            "-----------",
            "",
            "These figures come from repeated runs on one machine. They are not an average",
            "across hardware, and they should be read as an ordering rather than as",
            "absolute throughput you can expect elsewhere.",
            "",
            format_provenance(reports, libraries),
            "",
            "Reproducing this page",
            "---------------------",
            "",
            "From a checkout, with the ``dev`` and ``benchmark`` extras installed:",
            "",
            ".. code-block:: bash",
            "",
        ]
    )
    parts.extend(f"    {line}" for line in REPRODUCE_COMMAND.splitlines())
    parts.extend(
        [
            "",
            "The script runs a discarded warmup pass, then the suite several times, reads",
            "the pytest-benchmark JSON reports, and rewrites this page with the numbers and",
            "the environment it observed. Rerun it on your own machine before quoting any",
            "of these figures as your own.",
            "",
            "Caveats",
            "-------",
            "",
            "* Every figure is a median from one machine; a benchmark is a draw from a",
            "  noisy process, not a constant.",
            "* The fastest entries take well under a microsecond, which is only tens of",
            "  ticks of the platform timer, so their medians are coarsely quantized. Where",
            "  two adjacent entries were not separated by the measurement, the note under",
            "  the table says so and they should be read as tied.",
            "* Only the eight operations above are measured. A library that is slower here",
            "  may be faster on work this suite does not cover.",
            "* Install cost is not measured. ``pygeohash`` ships pre-built wheels and needs",
            "  no compiler at install time, which is what motivated the comparison in the",
            "  first place, but that is a packaging property rather than a speed result.",
            "",
        ]
    )
    return "\n".join(parts).rstrip("\n") + "\n"


def render_markdown_summary(reports):
    """Render a compact Markdown table for pasting into README.md."""
    lines = ["| Library | encode | decode | bbox |", "|---|---|---|---|"]
    groups = [group for group, _, _ in GROUPS]
    per_group = {group: {row["library"]: row for row in collect_rows(reports, group)} for group in groups}

    order = sorted(
        {library for group in groups for library in per_group[group]},
        key=lambda library: per_group["encode"].get(library, {}).get("median_ns", float("inf")),
    )
    for library in order:
        label = f"**{library}**" if library == "pygeohash" else library
        cells = []
        for group in groups:
            row = per_group[group].get(library)
            cells.append(f"{row['median_ns']:,.0f}" if row else "—")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    """Run the benchmarks and write the documentation page."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Path of the reStructuredText page to write (default: docs/source/benchmarks.rst)",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=DEFAULT_REPEATS,
        help=f"How many times to run the suite (default: {DEFAULT_REPEATS})",
    )
    parser.add_argument(
        "--no-warmup",
        action="store_true",
        help="Skip the discarded warmup pass that normally precedes the timed repeats",
    )
    parser.add_argument(
        "--report",
        action="append",
        dest="reports",
        help="Reuse an existing pytest-benchmark JSON report instead of running the suite; repeatable",
    )
    args = parser.parse_args()

    if args.reports:
        report_paths = args.reports
    else:
        report_paths = []
        for _ in range(max(1, args.repeats)):
            handle, path = tempfile.mkstemp(suffix=".json", prefix="pygeohash-benchmark-")
            os.close(handle)
            report_paths.append(path)
        run_benchmarks(report_paths, warmup_passes=0 if args.no_warmup else 1)

    reports = []
    for path in report_paths:
        with open(path) as report_file:
            reports.append(json.load(report_file))

    with open(args.output, "w") as page:
        page.write(render_page(reports))
    print(f"Wrote {args.output}")

    print("\nMedian times in nanoseconds, for README.md:\n")
    print(render_markdown_summary(reports))


if __name__ == "__main__":
    main()
