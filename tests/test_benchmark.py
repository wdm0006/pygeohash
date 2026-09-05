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


def test_get_adjacent_typical_benchmark(benchmark):
    """Benchmark typical (non-border) adjacent lookup."""
    result = benchmark(lambda: pgh.get_adjacent("u4pruyd", "top"))
    assert result == "u4pruyf"  # Pinned adjacency value


def test_get_adjacent_border_benchmark(benchmark):
    """Benchmark border-wrap adjacent lookup (recursive parent-descent case)."""
    result = benchmark(lambda: pgh.get_adjacent("u00000", "left"))
    assert result == "gbpbpb"  # Pinned antimeridian wrap


def test_is_valid_geohash_benchmark(benchmark):
    """Benchmark geohash validation of a 7-character hash."""
    result = benchmark(lambda: pgh.is_valid_geohash("u4pruyd"))
    assert result is True


if __name__ == "__main__":
    # Run benchmarks directly if file is executed
    print("Running encode benchmarks...")
    test_encode_benchmark()

    print("\nRunning decode benchmarks...")
    test_decode_benchmark()

    print("\nRunning distance benchmarks...")
    test_approximate_distance_benchmark()
    test_haversine_distance_benchmark()
