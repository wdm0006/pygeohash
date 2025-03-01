#!/usr/bin/env python
"""Generate visualization examples for PyGeoHash documentation.

This script generates sample plots using the PyGeoHash visualization module.
The plots are saved to the docs/source/_static/images directory.

Usage:
    python scripts/generate_viz_examples.py
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend

# Add the parent directory to the path so we can import pygeohash
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygeohash as pgh
from pygeohash.viz import plot_geohash, plot_geohashes, folium_map


def ensure_dir(directory):
    """Ensure that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def generate_single_geohash_plot():
    """Generate a plot of a single geohash."""
    print("Generating single geohash plot...")
    fig, ax = plot_geohash("9q8yyk", color="red", alpha=0.5)
    if fig is not None:
        fig.tight_layout()
    return fig


def generate_single_geohash_with_label_plot():
    """Generate a plot of a single geohash with label and center point."""
    print("Generating single geohash with label plot...")
    fig, ax = plot_geohash("9q8yyk", color="blue", alpha=0.5, show_center=True, show_label=True)
    if fig is not None:
        fig.tight_layout()
    return fig


def generate_multiple_geohashes_plot():
    """Generate a plot of multiple geohashes."""
    print("Generating multiple geohashes plot...")
    geohashes = ["9q8yyk", "9q8yym", "9q8yyj", "9q8yys"]
    fig, ax = plot_geohashes(geohashes, alpha=0.7)
    if fig is not None:
        fig.tight_layout()
    return fig


def generate_multiple_geohashes_with_labels_plot():
    """Generate a plot of multiple geohashes with labels."""
    print("Generating multiple geohashes with labels plot...")
    geohashes = ["9q8yyk", "9q8yym", "9q8yyj", "9q8yys"]
    labels = ["Home", "Work", "Park", "Store"]
    fig, ax = plot_geohashes(
        geohashes, labels=labels, show_labels=True, colors=["red", "blue", "green", "orange"], alpha=0.7
    )
    if fig is not None:
        fig.tight_layout()
    return fig


def generate_geohash_neighbors_plot():
    """Generate a plot of a geohash and its neighbors."""
    print("Generating geohash neighbors plot...")
    center = "9q8yyk"

    # Get all neighbors in each direction
    directions = ["top", "right", "bottom", "left"]
    direction_labels = {"top": "North", "right": "East", "bottom": "South", "left": "West"}

    neighbors = {}
    for direction in directions:
        neighbors[direction_labels[direction]] = pgh.get_adjacent(center, direction)

    all_geohashes = [center] + list(neighbors.values())
    labels = ["Center"] + list(neighbors.keys())

    fig, ax = plot_geohashes(
        all_geohashes, labels=labels, show_labels=True, colors=["red"] + ["blue"] * len(neighbors), alpha=0.7
    )
    if fig is not None:
        fig.tight_layout()
    return fig


def generate_geohash_precision_plot():
    """Generate a plot showing different geohash precisions."""
    print("Generating geohash precision plot...")
    # Start with a precision 4 geohash
    base_geohash = "9q8y"

    # Generate geohashes at different precisions
    geohashes = [
        base_geohash,
        base_geohash + "y",
        base_geohash + "yk",
    ]

    labels = [f"Precision {len(gh)}" for gh in geohashes]

    fig, ax = plot_geohashes(geohashes, labels=labels, show_labels=True, colors=["red", "green", "blue"], alpha=0.5)
    if fig is not None:
        fig.tight_layout()
    return fig


def generate_folium_map():
    """Generate an interactive folium map."""
    print("Generating folium map...")
    m = folium_map(center_geohash="9q8yyk", zoom_start=15)

    # Add a single geohash
    m.add_geohash("9q8yyk", color="red", popup="Home")

    # Add multiple geohashes with different colors
    m.add_geohashes(
        ["9q8yym", "9q8yyj", "9q8yys"], colors=["blue", "green", "orange"], popups=["Work", "Park", "Store"]
    )

    return m


def generate_folium_grid():
    """Generate an interactive folium map with a geohash grid."""
    print("Generating folium grid map...")
    m = folium_map(center_geohash="9q8y", zoom_start=12)

    # Add a geohash grid at precision 5
    m.add_geohash_grid(precision=5, fill_opacity=0.2)

    return m


def main():
    """Generate all visualization examples."""
    # Create output directory
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "source", "_static", "images"))
    ensure_dir(output_dir)

    # Generate static plots
    plots = {
        "single_geohash.png": generate_single_geohash_plot(),
        "single_geohash_labeled.png": generate_single_geohash_with_label_plot(),
        "multiple_geohashes.png": generate_multiple_geohashes_plot(),
        "multiple_geohashes_labeled.png": generate_multiple_geohashes_with_labels_plot(),
        "geohash_neighbors.png": generate_geohash_neighbors_plot(),
        "geohash_precision.png": generate_geohash_precision_plot(),
    }

    # Save static plots
    for filename, fig in plots.items():
        if fig is not None:  # Only save if the figure was created successfully
            filepath = os.path.join(output_dir, filename)
            fig.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close(fig)
            print(f"Saved {filepath}")
        else:
            print(f"Skipped {filename} - figure could not be created")

    # Generate interactive maps
    try:
        maps = {
            "folium_map.html": generate_folium_map(),
            "folium_grid.html": generate_folium_grid(),
        }

        # Save interactive maps
        for filename, m in maps.items():
            if m is not None:  # Check if folium is installed
                filepath = os.path.join(output_dir, filename)
                m.save(filepath)
                print(f"Saved {filepath}")
    except Exception as e:
        print(f"Error generating interactive maps: {e}")
        print("Skipping interactive maps")

    print("Done!")


if __name__ == "__main__":
    main()
