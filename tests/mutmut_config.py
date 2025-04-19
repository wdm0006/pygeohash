"""Mutmut configuration for pygeohash."""

import sys
import os
import re # Import regex module

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# --- Configuration Settings (moved from pyproject.toml) ---
paths_to_mutate = [
    "pygeohash/distances.py",
    "pygeohash/neighbor.py",
    "pygeohash/bounding_box.py",
    "pygeohash/stats.py",
    "pygeohash/types.py",
    "pygeohash/viz.py",
]
tests_dir = "tests" # Explicitly defining, though often auto-detected
runner = "make test"
backup = False
also_copy = [
    "pygeohash/cgeohash/*",
    "examples",
]
# ----------------------------------------------------------

def pre_mutation(context):
    """Runs before each mutation test. Skip logger lines."""
    # Get the source code line where the mutation would occur
    # context.current_source_line might be None in some edge cases, handle gracefully
    line = getattr(context, 'current_source_line', "")
    if line:
        line = line.strip()

    # Define the pattern to skip (lines starting with logger.debug, .info, .warning, .error, etc.)
    # Making it robust against potential leading whitespace
    log_pattern = r'^\s*logger\.(debug|info|warning|error|exception|critical)\(.*\)'

    if line and re.match(log_pattern, line):
        # print(f"Skipping logger line: {line}") # Optional: for debugging
        context.skip = True # Tell mutmut to skip this mutation

def post_mutation(context):
    """Runs after each mutation test."""
    pass 