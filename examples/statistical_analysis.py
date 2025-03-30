"""Example demonstrating statistical operations on geohashes.

This example shows how to perform statistical analysis on collections of geohashes:
1. Finding mean positions
2. Finding cardinal extremes (north, south, east, west)
3. Calculating variance and standard deviation
4. Working with distances between geohashes
"""

from pygeohash import (
    mean,
    northern,
    southern,
    eastern,
    western,
    variance,
    std,
    geohash_approximate_distance,
    geohash_haversine_distance,
    Geohash,
    GeohashCollection,
    assert_valid_geohash,
)


def demonstrate_cardinal_points() -> None:
    """Show how to find extreme points in a collection of geohashes."""
    print("\nCardinal Points:")
    print("---------------")

    # Sample geohashes around San Francisco Bay
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

    # Find extreme points
    print(f"Northernmost: {northern(geohashes)}")
    print(f"Southernmost: {southern(geohashes)}")
    print(f"Easternmost: {eastern(geohashes)}")
    print(f"Westernmost: {western(geohashes)}")


def demonstrate_mean_position() -> None:
    """Show how to find the mean position of geohashes."""
    print("\nMean Position:")
    print("-------------")

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

    # Calculate mean with different precisions
    for precision in [4, 6, 8]:
        center = assert_valid_geohash(mean(geohashes, precision=precision))
        print(f"Mean (precision {precision}): {center}")


def demonstrate_distances() -> None:
    """Show different ways to calculate distances between geohashes."""
    print("\nDistance Calculations:")
    print("--------------------")

    # Two points to measure distance between
    sf: Geohash = assert_valid_geohash("9q8yyk")  # San Francisco
    oak: Geohash = assert_valid_geohash("9q9k3p")  # Oakland

    # Calculate distances using different methods
    approx_dist = geohash_approximate_distance(sf, oak)
    exact_dist = geohash_haversine_distance(sf, oak)

    print(f"Approximate distance: {approx_dist:.0f} meters")
    print(f"Haversine distance: {exact_dist:.0f} meters")


def demonstrate_dispersion() -> None:
    """Show how to measure the dispersion of geohashes."""
    print("\nDispersion Statistics:")
    print("--------------------")

    # Sample geohashes (points around SF Bay)
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

    # Calculate variance and standard deviation
    var = variance(geohashes)
    std_dev = std(geohashes)

    print(f"Variance: {var:.0f} square meters")
    print(f"Standard deviation: {std_dev:.0f} meters")


def main() -> None:
    """Run all demonstrations."""
    print("Statistical Operations")
    print("=====================")

    demonstrate_cardinal_points()
    demonstrate_mean_position()
    demonstrate_distances()
    demonstrate_dispersion()


if __name__ == "__main__":
    main()
