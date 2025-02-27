import pytest
import importlib.util
import pygeohash as pgh

# Check if numpy and numba are available
numpy_available = importlib.util.find_spec("numpy") is not None
numba_available = importlib.util.find_spec("numba") is not None

# Import numpy if available
if numpy_available:
    import numpy as np

# Skip numba tests if not available
numba_skip = pytest.mark.skipif(
    not (numpy_available and numba_available), reason="Numpy and Numba are required for these tests"
)


def test_encode_benchmark(benchmark):
    """Benchmark standard geohash encoding."""
    result = benchmark(lambda: pgh.encode(42.6, -5.6))
    assert len(result) > 0  # Simple validation


@numba_skip
def test_numba_point_encode_benchmark(benchmark):
    """Benchmark Numba-accelerated point geohash encoding."""
    result = benchmark(lambda: pgh.nb_point_encode(42.6, -5.6))
    assert len(result) > 0  # Simple validation


@numba_skip
def test_numba_vector_encode_benchmark(benchmark):
    """Benchmark Numba-accelerated vector geohash encoding."""
    # Create test data
    size = 1000
    lat = np.full(size, 42.6)
    lon = np.full(size, -5.6)

    # Benchmark vector encoding
    result = benchmark(lambda: pgh.nb_vector_encode(lat, lon))
    assert len(result) == size  # Validate result size


def test_decode_benchmark(benchmark):
    """Benchmark standard geohash decoding."""
    result = benchmark(lambda: pgh.decode("ezs42"))
    assert result is not None  # Simple validation


@numba_skip
def test_numba_point_decode_benchmark(benchmark):
    """Benchmark Numba-accelerated point geohash decoding."""
    result = benchmark(lambda: pgh.nb_point_decode("ezs42"))
    assert result is not None  # Simple validation


@numba_skip
def test_numba_vector_decode_benchmark(benchmark):
    """Benchmark Numba-accelerated vector geohash decoding."""
    # Create test data
    size = 1000
    geohashes = np.array(["ezs42"] * size)

    # Benchmark vector decoding
    result = benchmark(lambda: pgh.nb_vector_decode(geohashes))
    assert len(result) == 2  # Should return lat and lon arrays


def test_approximate_distance_benchmark(benchmark):
    """Benchmark approximate distance calculation."""
    result = benchmark(lambda: pgh.geohash_approximate_distance("ezs42", "u4pruydqqvj"))
    assert result > 0  # Distance should be positive


def test_haversine_distance_benchmark(benchmark):
    """Benchmark haversine distance calculation."""
    result = benchmark(lambda: pgh.geohash_haversine_distance("ezs42", "u4pruydqqvj"))
    assert result > 0  # Distance should be positive


if __name__ == "__main__":
    # Run benchmarks directly if file is executed
    print("Running encode benchmarks...")
    test_encode_benchmark()
    if numpy_available and numba_available:
        test_numba_point_encode_benchmark()
        test_numba_vector_encode_benchmark()

    print("\nRunning decode benchmarks...")
    test_decode_benchmark()
    if numpy_available and numba_available:
        test_numba_point_decode_benchmark()
        test_numba_vector_decode_benchmark()

    print("\nRunning distance benchmarks...")
    test_approximate_distance_benchmark()
    test_haversine_distance_benchmark()
