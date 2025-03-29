"""Tests for example scripts.

This module tests that all example scripts can run without errors.
Each test captures stdout and verifies expected output is present.
"""

import io
import sys
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before other imports

from contextlib import redirect_stdout
from pathlib import Path
from examples import basic_operations
from examples import statistical_analysis
from examples import visualization_examples
from examples import typed_data_analysis

# Add examples directory to path
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
sys.path.append(str(EXAMPLES_DIR))


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


def test_visualization_examples():
    """Test visualization_examples.py example runs without errors."""
    output = capture_output(visualization_examples.main)

    # Verify key sections are present
    assert "Visualization Examples" in output
    assert "Plotting single geohash" in output
    assert "Plotting multiple geohashes" in output
    assert "Creating Folium map" in output

    # Verify files were created
    images_dir = EXAMPLES_DIR / "images"
    assert (images_dir / "single_geohash.png").exists()
    assert (images_dir / "multiple_geohashes.png").exists()
    assert (images_dir / "tech_companies.html").exists()


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
