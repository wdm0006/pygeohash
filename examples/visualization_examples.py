"""Example demonstrating visualization capabilities of pygeohash.

This example shows how to create different types of visualizations:
1. Basic geohash plots
2. Multiple geohash plots with different colors
3. Interactive Folium maps
4. Saving visualizations to files
"""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt

from pygeohash import (
    plot_geohash,
    plot_geohashes,
    folium_map,
    get_bounding_box,
    Geohash,
    GeohashCollection,
    assert_valid_geohash,
)

# Default output directory for the generated images
IMAGES_DIR = Path(__file__).parent / "images"


def demonstrate_single_geohash(output_dir: Path) -> None:
    """Show how to plot a single geohash.

    Args:
        output_dir: Directory the generated PNG is written to.
    """
    print("\nPlotting single geohash...")

    # Plot San Francisco geohash
    geohash: Geohash = assert_valid_geohash("9q8yyk")
    plot_geohash(geohash)

    # Add title and save
    plt.title("San Francisco Geohash")
    plt.savefig(output_dir / "single_geohash.png")
    plt.close()


def demonstrate_multiple_geohashes(output_dir: Path) -> None:
    """Show how to plot multiple geohashes with different styles.

    Args:
        output_dir: Directory the generated PNG is written to.
    """
    print("\nPlotting multiple geohashes...")

    # Sample geohashes around SF Bay
    geohashes: GeohashCollection = [
        assert_valid_geohash(gh)
        for gh in [
            "9q8yyk",  # San Francisco
            "9q9k3p",  # Oakland
            "9q9jh7",  # Berkeley
            "9q9j8p",  # Alameda
            "9q8vx4",  # Daly City
        ]
    ]

    # Plot with different colors
    colors = ["red", "blue", "green", "purple", "orange"]
    plot_geohashes(geohashes, colors=colors)

    # Add title and save
    plt.title("SF Bay Area Geohashes")
    plt.savefig(output_dir / "multiple_geohashes.png")
    plt.close()


def demonstrate_folium_map(output_dir: Path) -> None:
    """Show how to create an interactive Folium map.

    Args:
        output_dir: Directory the generated HTML map is written to.
    """
    print("\nCreating Folium map...")

    # Sample geohashes (Silicon Valley tech companies)
    geohashes: GeohashCollection = [
        assert_valid_geohash(gh)
        for gh in [
            "9q9fs6",  # Apple Park
            "9q9f27",  # Google
            "9q9j85",  # Meta
            "9q9hvp",  # Tesla Factory
        ]
    ]

    # Create map centered on first geohash
    bbox = get_bounding_box(geohashes[0])
    center_lat = (bbox.min_lat + bbox.max_lat) / 2
    center_lon = (bbox.min_lon + bbox.max_lon) / 2

    # Create and save map
    m = folium_map(
        center=(center_lat, center_lon),
        zoom_start=10,
    )

    # Add geohashes to map
    m.add_geohashes(
        geohashes,
        colors=["red", "blue", "green", "purple"],
        tooltips=["Apple", "Google", "Meta", "Tesla"],
    )
    m.save(output_dir / "tech_companies.html")


def main(output_dir: Optional[Path] = None) -> None:
    """Run all demonstrations.

    Args:
        output_dir: Directory the generated files are written to. Defaults to the
            ``images`` directory next to this script.
    """
    output_dir = IMAGES_DIR if output_dir is None else Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Visualization Examples")
    print("====================")

    demonstrate_single_geohash(output_dir)
    demonstrate_multiple_geohashes(output_dir)
    demonstrate_folium_map(output_dir)

    print(f"\nVisualization files saved in: {output_dir}")


if __name__ == "__main__":
    main()
