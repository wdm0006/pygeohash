import pygeohash as pgh


def test_encode_benchmark(benchmark):
    """Benchmark standard geohash encoding."""
    result = benchmark(lambda: pgh.encode(42.6, -5.6))
    assert len(result) > 0  # Simple validation


def test_decode_benchmark(benchmark):
    """Benchmark standard geohash decoding."""
    result = benchmark(lambda: pgh.decode("ezs42"))
    assert result is not None  # Simple validation


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

    print("\nRunning decode benchmarks...")
    test_decode_benchmark()

    print("\nRunning distance benchmarks...")
    test_approximate_distance_benchmark()
    test_haversine_distance_benchmark()
