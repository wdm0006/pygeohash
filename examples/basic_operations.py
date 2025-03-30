"""Example demonstrating basic geohash operations.

This example shows the core functionality of pygeohash:
1. Encoding coordinates to geohashes
2. Decoding geohashes to coordinates
3. Finding adjacent geohashes
4. Working with different precision levels
"""

from pygeohash import (
    encode,
    decode,
    encode_strictly,
    decode_exactly,
    get_adjacent,
    assert_valid_geohash,
    assert_valid_latitude,
    assert_valid_longitude,
)


def demonstrate_encoding() -> None:
    """Show different ways to encode coordinates to geohashes."""
    print("\nEncoding Examples:")
    print("-----------------")

    # Basic encoding
    lat = assert_valid_latitude(37.7749)
    lon = assert_valid_longitude(-122.4194)

    # Different precision levels
    for precision in [4, 6, 8, 10]:
        geohash = assert_valid_geohash(encode(lat, lon, precision))
        print(f"Precision {precision}: {geohash}")

    # Strict encoding (handles edge cases differently)
    strict_geohash = assert_valid_geohash(encode_strictly(lat, lon, precision=7))
    print(f"Strict encoding: {strict_geohash}")


def demonstrate_decoding() -> None:
    """Show different ways to decode geohashes to coordinates."""
    print("\nDecoding Examples:")
    print("-----------------")

    geohash = assert_valid_geohash("9q8yyk")

    # Basic decoding
    location = decode(geohash)
    print(f"Basic decoding: ({location.latitude}, {location.longitude})")

    # Exact decoding with error margins
    exact = decode_exactly(geohash)
    print(f"Exact decoding: ({exact.latitude} ± {exact.latitude_error}, {exact.longitude} ± {exact.longitude_error})")


def demonstrate_neighbors() -> None:
    """Show how to find adjacent geohashes."""
    print("\nNeighbor Examples:")
    print("-----------------")

    geohash = assert_valid_geohash("9q8yyk")
    print(f"Original: {geohash}")

    # Get neighbors in each direction
    for direction in ["top", "right", "bottom", "left"]:
        neighbor = assert_valid_geohash(get_adjacent(geohash, direction))
        print(f"{direction.capitalize()}: {neighbor}")


def main() -> None:
    """Run all demonstrations."""
    print("Basic Geohash Operations")
    print("=======================")

    demonstrate_encoding()
    demonstrate_decoding()
    demonstrate_neighbors()


if __name__ == "__main__":
    main()
