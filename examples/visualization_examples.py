"""Example demonstrating visualization capabilities of pygeohash.

This example shows how to create different types of visualizations:
1. Basic geohash plots
2. Multiple geohash plots with different colors
3. Interactive Folium maps
4. Saving visualizations to files
"""

from pathlib import Path

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

# Ensure images directory exists
IMAGES_DIR = Path(__file__).parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)


def demonstrate_single_geohash() -> None:
    """Show how to plot a single geohash."""
    print("\nPlotting single geohash...")

    # Plot San Francisco geohash
    geohash: Geohash = assert_valid_geohash("9q8yyk")
    plot_geohash(geohash)

    # Add title and save
    plt.title("San Francisco Geohash")
    plt.savefig(IMAGES_DIR / "single_geohash.png")
    plt.close()


def demonstrate_multiple_geohashes() -> None:
    """Show how to plot multiple geohashes with different styles."""
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
    plt.savefig(IMAGES_DIR / "multiple_geohashes.png")
    plt.close()


def demonstrate_folium_map() -> None:
    """Show how to create an interactive Folium map."""
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
    m.save(IMAGES_DIR / "tech_companies.html")


def main() -> None:
    """Run all demonstrations."""
    print("Visualization Examples")
    print("====================")

    demonstrate_single_geohash()
    demonstrate_multiple_geohashes()
    demonstrate_folium_map()

    print(f"\nVisualization files saved in: {IMAGES_DIR}")


if __name__ == "__main__":
    main()
