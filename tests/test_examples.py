"""Tests for example scripts.

This module tests that all example scripts can run without errors.
Each test captures stdout and verifies expected output is present.
"""

import hashlib
import io
import sys
import matplotlib

matplotlib.use("Agg")  # Set non-interactive backend before other imports

from contextlib import redirect_stdout
from pathlib import Path
from examples import basic_operations
from examples import statistical_analysis
from examples import visualization_examples
from examples import typed_data_analysis

# Add examples directory to path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
sys.path.append(str(EXAMPLES_DIR))

# Files under examples/images/ that are tracked in git and must survive a test run
TRACKED_IMAGE_NAMES = ("single_geohash.png", "multiple_geohashes.png", "tech_companies.html")


def _snapshot_tracked_images() -> dict:
    """Snapshot the tracked example images, keyed by file name.

    Records a content hash and the modification time. The mtime matters: regenerating
    these PNGs is byte-deterministic for a given matplotlib version, so a stray write
    can reproduce the committed bytes exactly and a content-only check would miss it.
    """
    images_dir = EXAMPLES_DIR / "images"
    return {
        name: (hashlib.sha256((images_dir / name).read_bytes()).hexdigest(), (images_dir / name).stat().st_mtime_ns)
        for name in TRACKED_IMAGE_NAMES
    }


def capture_output(func) -> str:
    """Capture stdout from a function.

    Args:
        func: Function to execute and capture output from

    Returns:
        str: Captured stdout
    """
    output = io.StringIO()
    with redirect_stdout(output):
        func()
    return output.getvalue()


def test_basic_operations():
    """Test basic_operations.py example runs without errors."""
    output = capture_output(basic_operations.main)

    # Verify key sections are present
    assert "Basic Geohash Operations" in output
    assert "Encoding Examples:" in output
    assert "Decoding Examples:" in output
    assert "Neighbor Examples:" in output

    # Verify some expected outputs
    assert "Precision" in output  # Should show different precision levels
    assert "Basic decoding: (" in output  # Should show decoded coordinates
    assert "Original:" in output  # Should show original geohash
    assert "Top:" in output  # Should show neighbor in top direction


def test_statistical_analysis():
    """Test statistical_analysis.py example runs without errors."""
    output = capture_output(statistical_analysis.main)

    # Verify key sections are present
    assert "Statistical Operations" in output
    assert "Cardinal Points:" in output
    assert "Mean Position:" in output
    assert "Distance Calculations:" in output
    assert "Dispersion Statistics:" in output

    # Verify some expected outputs
    assert "Northernmost:" in output  # Should show cardinal points
    assert "Mean (precision" in output  # Should show mean with different precisions
    assert "Approximate distance:" in output  # Should show distance calculations
    assert "Standard deviation:" in output  # Should show dispersion stats


def test_visualization_examples(tmp_path):
    """Test visualization_examples.py example runs without errors."""
    tracked_before = _snapshot_tracked_images()

    output = capture_output(lambda: visualization_examples.main(tmp_path))

    # Verify key sections are present
    assert "Visualization Examples" in output
    assert "Plotting single geohash" in output
    assert "Plotting multiple geohashes" in output
    assert "Creating Folium map" in output

    # Verify files were created, under the injected output directory
    for name in TRACKED_IMAGE_NAMES:
        assert (tmp_path / name).exists()

    # The example must not touch the tracked copies under examples/images/
    assert _snapshot_tracked_images() == tracked_before


def test_typed_data_analysis():
    """Test typed_data_analysis.py example runs without errors."""
    output = capture_output(typed_data_analysis.main)

    # Verify key sections are present
    assert "Creating sample data" in output
    assert "Accessing typed columns" in output
    assert "Converting to NumPy arrays" in output
    assert "Calculating center point" in output
    assert "Demonstrating error handling" in output

    # Verify some expected outputs
    assert "First geohash:" in output  # Should show geohash value
    assert "Center coordinate:" in output  # Should show center calculation
    assert "Caught error:" in output  # Should show error handling
