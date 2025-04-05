#!/usr/bin/env python
"""
Script to generate geohash test data from geohash.org.

This script fetches geohash data from geohash.org for a set of coordinates
and precision levels, and outputs the data in a format that can be used
in the reference dataset.

Usage:
    python scripts/generate_geohash_test_data.py [--count COUNT] [--output OUTPUT]

Options:
    --count COUNT     Number of random test cases to generate per precision level [default: 5]
    --output OUTPUT   Output file path [default: stdout]
"""

import argparse
import random
import requests
import sys
import time
from typing import Dict, List, Tuple

# Try to import pygeohash, but don't fail if it's not available
try:
    import pygeohash as pgh
except ImportError:
    print("Warning: pygeohash not found. Using geohash.org for all operations.")
    pgh = None

# Constants
MIN_LAT, MAX_LAT = -90.0, 90.0
MIN_LON, MAX_LON = -180.0, 180.0
PRECISION_LEVELS = [1, 3, 5, 7, 9, 12]  # Common precision levels


def generate_random_coordinates(count: int) -> List[Tuple[float, float]]:
    """Generate random latitude/longitude pairs."""
    return [
        (round(random.uniform(MIN_LAT, MAX_LAT), 6), round(random.uniform(MIN_LON, MAX_LON), 6))
        for _ in range(count)  # noqa: S311
    ]


def fetch_geohash_org_data(lat: float, lon: float, precision: int) -> Dict:
    """Fetch geohash data from geohash.org."""
    # If pygeohash is available, use it to encode the coordinates
    if pgh:
        geohash = pgh.encode(lat, lon, precision)
    else:
        # Otherwise, fetch a geohash at a higher precision and truncate
        # This is a fallback and not ideal
        base_url = f"http://geohash.org/{lat},{lon}.json"
        response = requests.get(base_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        geohash = data.get("geohash", "")[:precision]

    # Construct URL for the geohash.org API
    base_url = f"http://geohash.org/{geohash}.json"

    # Add delay to avoid overwhelming the server
    time.sleep(0.5)

    try:
        response = requests.get(base_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for {lat}, {lon}, precision {precision}: {e}", file=sys.stderr)
        return None


def generate_test_data(count_per_precision: int) -> List[Dict]:
    """Generate test data for various coordinates and precision levels."""
    results = []

    # Generate random coordinates
    coordinates = generate_random_coordinates(count_per_precision)

    # For each coordinate, fetch data for all precision levels
    for lat, lon in coordinates:
        precision_map = {}

        for precision in PRECISION_LEVELS:
            print(f"Fetching data for ({lat}, {lon}) at precision {precision}...", file=sys.stderr)
            data = fetch_geohash_org_data(lat, lon, precision)

            if data and "geohash" in data:
                precision_map[precision] = data["geohash"]
            else:
                print(f"Failed to fetch data for ({lat}, {lon}) at precision {precision}", file=sys.stderr)

        if precision_map:
            results.append(
                {"lat": lat, "lon": lon, "precision_map": precision_map, "description": f"Random point ({lat}, {lon})"}
            )

    return results


def format_as_python_code(data: List[Dict]) -> str:
    """Format the test data as Python code for inclusion in the reference dataset."""
    code = "# Generated test cases\n"
    code += "GENERATED_CASES = [\n"

    for item in data:
        code += f"    # {item['description']}\n"
        code += f"    ({item['lat']}, {item['lon']}, {{\n"

        for precision, geohash in sorted(item["precision_map"].items()):
            code += f'        {precision}: "{geohash}",\n'

        code += "    }}),\n"

    code += "]\n"
    return code


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate geohash test data from geohash.org")
    parser.add_argument(
        "--count", type=int, default=5, help="Number of random test cases to generate per precision level"
    )
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")

    args = parser.parse_args()

    # Generate test data
    data = generate_test_data(args.count)

    # Format as Python code
    code = format_as_python_code(data)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(code)
        print(f"Test data written to {args.output}", file=sys.stderr)
    else:
        print(code)


if __name__ == "__main__":
    main()
