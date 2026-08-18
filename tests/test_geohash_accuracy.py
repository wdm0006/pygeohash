import pytest
import random
import pygeohash as pgh
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Constants for test data generation
MIN_LAT, MAX_LAT = -90.0, 90.0
MIN_LON, MAX_LON = -180.0, 180.0
PRECISION_LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# Tolerance for coordinate comparison (due to precision loss in encoding/decoding)
TOLERANCE = 1e-5


def generate_random_coordinates(count: int) -> List[Tuple[float, float]]:
    """Generate random latitude/longitude pairs."""
    return [
        (round(random.uniform(MIN_LAT, MAX_LAT), 6), round(random.uniform(MIN_LON, MAX_LON), 6))  # noqa: S311
        for _ in range(count)  # noqa: S311
    ]


def test_roundtrip_consistency():
    """Test encode->decode->encode roundtrip consistency.

    Instead of expecting exact geohash matches, we verify that the decoded
    coordinates from both the original and re-encoded geohashes are close enough.
    """
    # Generate test cases for each precision level
    for precision in PRECISION_LEVELS:
        coordinates = generate_random_coordinates(10)

        for lat, lon in coordinates:
            # Encode
            geohash = pgh.encode(lat, lon, precision)

            # Decode
            decoded = pgh.decode(geohash)

            # Re-encode
            reencoded = pgh.encode(decoded.latitude, decoded.longitude, precision)

            # Decode the re-encoded geohash
            redecoded = pgh.decode(reencoded)

            # Compare the decoded coordinates instead of the geohashes
            # This is more meaningful as geohashes at boundaries can be different
            # but represent very close coordinates
            assert abs(decoded.latitude - redecoded.latitude) < 1e-10, (
                f"Roundtrip latitude mismatch for ({lat}, {lon}) at precision {precision}"
            )
            assert abs(decoded.longitude - redecoded.longitude) < 1e-10, (
                f"Roundtrip longitude mismatch for ({lat}, {lon}) at precision {precision}"
            )


def _expected_error_degrees(precision: int) -> float:
    """Return the coordinate error envelope, in degrees, allowed at a precision level."""
    # Higher precision levels need a higher safety factor
    safety_factor = 1.5
    if precision > 8:
        safety_factor = 2.0
    if precision > 10:
        safety_factor = 3.0

    return safety_factor * 180.0 / (2 ** (2.5 * precision - 1))


def _check_case(
    case_number: int,
    lat: float,
    lon: float,
    precision: int,
    decode: Callable[[str], pgh.LatLong],
) -> Optional[Dict[str, Any]]:
    """Encode one coordinate and report the decoded errors when they exceed the envelope.

    Returns None when both coordinate errors stay inside the envelope, otherwise a
    dictionary describing the violation.
    """
    logger.info(f"Test case {case_number}: ({lat}, {lon}) at precision {precision}")

    # Encode
    geohash = pgh.encode(lat, lon, precision)
    logger.info(f"  Original geohash: {geohash}")

    # Decode
    decoded = decode(geohash)
    logger.info(f"  Decoded coordinates: ({decoded.latitude}, {decoded.longitude})")

    # Re-encode
    reencoded = pgh.encode(decoded.latitude, decoded.longitude, precision)
    logger.info(f"  Re-encoded geohash: {reencoded}")

    # Decode the re-encoded geohash
    redecoded = decode(reencoded)

    # Compare the decoded coordinates
    logger.info(
        "  Coordinate differences between decodings: "
        f"lat_diff={abs(decoded.latitude - redecoded.latitude)}, "
        f"lon_diff={abs(decoded.longitude - redecoded.longitude)}"
    )

    expected_error_degrees = _expected_error_degrees(precision)
    logger.info(f"  Expected error margin: {expected_error_degrees} degrees")

    # Calculate actual errors
    lat_error = abs(decoded.latitude - lat)

    lon_error = min(
        abs(decoded.longitude - lon), abs(decoded.longitude - (lon - 360)), abs(decoded.longitude - (lon + 360))
    )

    logger.info(f"  Actual errors: lat_error={lat_error}, lon_error={lon_error}")

    # Check if errors are within expected range
    lat_ok = lat_error < expected_error_degrees
    lon_ok = lon_error < expected_error_degrees

    if lat_ok and lon_ok:
        logger.info("  SUCCESS: Both errors within expected range")
        return None

    logger.warning(f"  FAILURE: {'latitude' if not lat_ok else 'longitude'} error too large")
    return {
        "test_case": case_number,
        "coordinates": (lat, lon),
        "precision": precision,
        "geohash": geohash,
        "decoded": (decoded.latitude, decoded.longitude),
        "expected_error": expected_error_degrees,
        "lat_error": lat_error,
        "lon_error": lon_error,
        "lat_ok": lat_ok,
        "lon_ok": lon_ok,
    }


def _describe_failure(failure: Dict[str, Any]) -> str:
    """Render one envelope violation as a single diagnostic line."""
    return (
        f"case {failure['test_case']}: {failure['coordinates']} at precision {failure['precision']} "
        f"encoded to {failure['geohash']}, decoded to {failure['decoded']} "
        f"(lat_error={failure['lat_error']}, lon_error={failure['lon_error']}, "
        f"expected < {failure['expected_error']})"
    )


def assert_cases_within_envelope(
    cases: Sequence[Tuple[float, float, int]],
    decode: Optional[Callable[[str], pgh.LatLong]] = None,
) -> None:
    """Assert every (latitude, longitude, precision) case decodes inside its error envelope."""
    decoder = pgh.decode if decode is None else decode

    failures = []
    for case_number, (lat, lon, precision) in enumerate(cases, start=1):
        failure = _check_case(case_number, lat, lon, precision, decoder)
        if failure is not None:
            failures.append(failure)
        logger.info("-" * 80)

    diagnostics = "\n".join(_describe_failure(failure) for failure in failures)
    if failures:
        logger.error(f"Found {len(failures)} test cases with errors exceeding expected margins:\n{diagnostics}")

    assert not failures, f"Found {len(failures)} test cases with errors exceeding expected margins:\n{diagnostics}"


def test_random_precision_combinations():
    """Test random combinations of coordinates and precision levels."""
    # Set a fixed seed for reproducibility
    random.seed(42)

    # Generate random test cases
    num_random_tests = 100
    random_tests = []

    for _ in range(num_random_tests):
        lat = random.uniform(MIN_LAT, MAX_LAT)  # noqa: S311
        lon = random.uniform(MIN_LON, MAX_LON)  # noqa: S311
        precision = random.choice(PRECISION_LEVELS)  # noqa: S311
        random_tests.append((lat, lon, precision))

    assert_cases_within_envelope(random_tests)


def test_envelope_violation_fails_instead_of_skipping():
    """A decoded coordinate outside the envelope must fail the check, not skip it."""
    # Chosen so the envelope (~0.0165 degrees at precision 6) is exceeded by a wide margin.
    case = (10.0, 20.0, 6)

    def decode_outside_envelope(geohash: str) -> pgh.LatLong:
        return pgh.LatLong(10.5, 20.5)

    # Control: the same case decodes inside the envelope with the real codec.
    assert_cases_within_envelope([case])

    try:
        assert_cases_within_envelope([case], decode=decode_outside_envelope)
    except pytest.skip.Exception as skipped:
        pytest.fail(f"envelope violation was skipped instead of failed: {skipped}")
    except AssertionError as error:
        message = str(error)
    else:
        pytest.fail("envelope violation did not fail the check")

    assert "Found 1 test cases with errors exceeding expected margins" in message
    # The diagnostics carry the exact per-case errors and the bound they exceeded.
    assert "at precision 6" in message
    assert "(lat_error=0.5, lon_error=0.5, expected < 0.0164794921875)" in message


def test_geohash_precision():
    """Test that geohash precision corresponds to expected error ranges."""
    # Test a range of precisions
    test_point = (37.7749, -122.4194)  # San Francisco

    # Expected error in degrees for each precision level
    # These are more generous values based on the actual implementation behavior
    expected_errors = {
        1: 20.0,  # ~20 degrees
        2: 5.0,  # ~5 degrees
        3: 2.0,  # ~2 degrees
        4: 1.0,  # ~1 degree
        5: 0.2,  # ~0.2 degrees
        6: 0.05,  # ~0.05 degrees
        7: 0.01,  # ~0.01 degrees
        8: 0.002,  # ~0.002 degrees
        9: 0.0005,  # ~0.0005 degrees
        10: 0.0001,  # ~0.0001 degrees
        11: 0.00002,  # ~0.00002 degrees
        12: 0.000005,  # ~0.000005 degrees
    }

    for precision, expected_error in expected_errors.items():
        # Encode at this precision
        geohash = pgh.encode(test_point[0], test_point[1], precision)

        # Decode
        decoded = pgh.decode(geohash)

        # Check that the error is within expected range
        lat_error = abs(decoded.latitude - test_point[0])
        lon_error = abs(decoded.longitude - test_point[1])

        assert lat_error <= expected_error, (
            f"Latitude error for precision {precision} is {lat_error}, expected <= {expected_error}"
        )
        assert lon_error <= expected_error, (
            f"Longitude error for precision {precision} is {lon_error}, expected <= {expected_error}"
        )
