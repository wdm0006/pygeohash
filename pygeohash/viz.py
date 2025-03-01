"""Visualization module for PyGeoHash.

This module provides functions for visualizing geohashes on maps.
It requires additional dependencies that can be installed with:
    pip install pygeohash[viz]

Functions:
    plot_geohash: Plot a single geohash on a map
    plot_geohashes: Plot multiple geohashes on a map
    folium_map: Create an interactive map with geohashes using Folium
"""

import warnings
from typing import List, Optional, Tuple, Union

from .geohash import decode
from .bounding_box import get_bounding_box, geohashes_in_box, BoundingBox


def _check_viz_dependencies() -> bool:
    """Check if visualization dependencies are installed.

    Returns:
        bool: True if dependencies are installed, False otherwise
    """
    try:
        import matplotlib  # noqa: F401

        return True
    except ImportError:
        warnings.warn(
            "Matplotlib is required for visualization functions. Install with: pip install pygeohash[viz]",
            stacklevel=2
        )
        return False


def _check_folium_dependencies() -> bool:
    """Check if folium dependencies are installed.

    Returns:
        bool: True if dependencies are installed, False otherwise
    """
    try:
        import folium  # noqa: F401

        return True
    except ImportError:
        warnings.warn(
            "Folium is required for interactive maps. Install with: pip install pygeohash[viz]",
            stacklevel=2
        )
        return False


def plot_geohash(
    geohash: str,
    ax=None,
    color: str = "red",
    alpha: float = 0.5,
    label: Optional[str] = None,
    show_center: bool = False,
    show_label: bool = False,
    **kwargs,
) -> Tuple:
    """Plot a single geohash on a map.

    Args:
        geohash: The geohash string to plot
        ax: Matplotlib axis to plot on (optional)
        color: Color of the geohash polygon
        alpha: Transparency of the geohash polygon
        label: Label for the geohash (defaults to the geohash string)
        show_center: Whether to show the center point of the geohash
        show_label: Whether to show the label on the map
        **kwargs: Additional keyword arguments passed to matplotlib

    Returns:
        Tuple: (fig, ax) - The matplotlib figure and axis objects

    Examples:
        >>> import pygeohash as pgh
        >>> from pygeohash.viz import plot_geohash
        >>> fig, ax = plot_geohash("9q8yyk")
    """
    if not _check_viz_dependencies():
        return None, None

    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    # Create figure and axis if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    else:
        fig = ax.figure

    # Get bounding box for the geohash
    bbox = get_bounding_box(geohash)

    # Calculate width and height
    width = bbox.max_lon - bbox.min_lon
    height = bbox.max_lat - bbox.min_lat

    # Create rectangle
    rect = Rectangle(
        (bbox.min_lon, bbox.min_lat),
        width,
        height,
        linewidth=1,
        edgecolor=color,
        facecolor=color,
        alpha=alpha,
        **kwargs,
    )

    # Add rectangle to plot
    ax.add_patch(rect)

    # Show center point if requested
    if show_center:
        center_lat = (bbox.min_lat + bbox.max_lat) / 2
        center_lon = (bbox.min_lon + bbox.max_lon) / 2
        ax.plot(center_lon, center_lat, "o", color="black")

    # Add label if requested
    if show_label:
        center_lat = (bbox.min_lat + bbox.max_lat) / 2
        center_lon = (bbox.min_lon + bbox.max_lon) / 2
        ax.text(center_lon, center_lat, label or geohash, ha="center", va="center", fontsize=8, color="black")

    # Set axis limits with a small buffer
    buffer = max(width, height) * 0.1
    ax.set_xlim(bbox.min_lon - buffer, bbox.max_lon + buffer)
    ax.set_ylim(bbox.min_lat - buffer, bbox.max_lat + buffer)

    # Add grid for better orientation
    ax.grid(True, linestyle="--", alpha=0.6)

    # Set labels and title
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Geohash: {geohash}")

    # Make sure aspect ratio is equal
    ax.set_aspect("equal", "box")

    return fig, ax


def plot_geohashes(
    geohashes: List[str],
    ax=None,
    colors: Union[str, List[str]] = "viridis",
    alpha: float = 0.5,
    labels: Optional[List[str]] = None,
    show_centers: bool = False,
    show_labels: bool = False,
    **kwargs,
) -> Tuple:
    """Plot multiple geohashes on a map.

    Args:
        geohashes: List of geohash strings to plot
        ax: Matplotlib axis to plot on (optional)
        colors: Color or colormap name for the geohashes
        alpha: Transparency of the geohash polygons
        labels: Labels for the geohashes (defaults to the geohash strings)
        show_centers: Whether to show the center points of the geohashes
        show_labels: Whether to show the labels on the map
        **kwargs: Additional keyword arguments passed to matplotlib

    Returns:
        Tuple: (fig, ax) - The matplotlib figure and axis objects

    Examples:
        >>> import pygeohash as pgh
        >>> from pygeohash.viz import plot_geohashes
        >>> fig, ax = plot_geohashes(["9q8yyk", "9q8yym", "9q8yyj"])
    """
    if not _check_viz_dependencies():
        return None, None

    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    from matplotlib.patches import Rectangle

    # Create figure and axis if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    else:
        fig = ax.figure

    # Set up colors
    n_geohashes = len(geohashes)
    if isinstance(colors, str):
        # If a colormap name is provided
        try:
            cmap = cm.get_cmap(colors, n_geohashes)
            colors = [cmap(i) for i in range(n_geohashes)]
        except ValueError:
            # If a single color name is provided
            colors = [colors] * n_geohashes
    elif len(colors) < n_geohashes:
        # If not enough colors are provided
        colors = colors * (n_geohashes // len(colors) + 1)
        colors = colors[:n_geohashes]

    # Set up labels
    if labels is None:
        labels = geohashes
    elif len(labels) < n_geohashes:
        labels = list(labels) + geohashes[len(labels) :]

    # Track the overall bounding box
    min_lon, min_lat = float("inf"), float("inf")
    max_lon, max_lat = float("-inf"), float("-inf")

    # Plot each geohash
    for i, geohash in enumerate(geohashes):
        # Get bounding box for the geohash
        bbox = get_bounding_box(geohash)

        # Update overall bounding box
        min_lon = min(min_lon, bbox.min_lon)
        min_lat = min(min_lat, bbox.min_lat)
        max_lon = max(max_lon, bbox.max_lon)
        max_lat = max(max_lat, bbox.max_lat)

        # Calculate width and height
        width = bbox.max_lon - bbox.min_lon
        height = bbox.max_lat - bbox.min_lat

        # Create rectangle
        rect = Rectangle(
            (bbox.min_lon, bbox.min_lat),
            width,
            height,
            linewidth=1,
            edgecolor=colors[i],
            facecolor=colors[i],
            alpha=alpha,
            label=labels[i] if i == 0 or labels[i] != labels[i - 1] else None,
            **kwargs,
        )

        # Add rectangle to plot
        ax.add_patch(rect)

        # Show center point if requested
        if show_centers:
            center_lat = (bbox.min_lat + bbox.max_lat) / 2
            center_lon = (bbox.min_lon + bbox.max_lon) / 2
            ax.plot(center_lon, center_lat, "o", color="black")

        # Add label if requested
        if show_labels:
            center_lat = (bbox.min_lat + bbox.max_lat) / 2
            center_lon = (bbox.min_lon + bbox.max_lon) / 2
            ax.text(center_lon, center_lat, labels[i], ha="center", va="center", fontsize=8, color="black")

    # Set axis limits with a small buffer
    width = max_lon - min_lon
    height = max_lat - min_lat
    buffer = max(width, height) * 0.1
    ax.set_xlim(min_lon - buffer, max_lon + buffer)
    ax.set_ylim(min_lat - buffer, max_lat + buffer)

    # Add grid for better orientation
    ax.grid(True, linestyle="--", alpha=0.6)

    # Set labels and title
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Geohashes: {len(geohashes)}")

    # Add legend if there are multiple geohashes with different labels
    if len(set(labels)) > 1:
        ax.legend()

    # Make sure aspect ratio is equal
    ax.set_aspect("equal", "box")

    return fig, ax


def folium_map(
    center_geohash: Optional[str] = None,
    center: Optional[Tuple[float, float]] = None,
    zoom_start: int = 13,
    tiles: str = "OpenStreetMap",
    width: str = "100%",
    height: str = "100%",
):
    """Create an interactive map with geohashes using Folium.

    Args:
        center_geohash: Geohash string to center the map on
        center: (lat, lon) tuple to center the map on (alternative to center_geohash)
        zoom_start: Initial zoom level
        tiles: Map tile provider
        width: Width of the map
        height: Height of the map

    Returns:
        folium.Map: A Folium map object with methods to add geohashes

    Examples:
        >>> import pygeohash as pgh
        >>> from pygeohash.viz import folium_map
        >>> m = folium_map(center_geohash="9q8yyk")
        >>> m.add_geohash("9q8yyk", color="red", fill=True)
        >>> m.save("geohash_map.html")
    """
    if not _check_folium_dependencies():
        return None

    import folium

    # Determine center coordinates
    if center_geohash is not None:
        lat, lon = decode(center_geohash)
        center = (lat, lon)
    elif center is None:
        # Default to San Francisco if no center is provided
        center = (37.7749, -122.4194)

    # Create map
    m = folium.Map(location=center, zoom_start=zoom_start, tiles=tiles, width=width, height=height)

    # Add method to add a single geohash
    def add_geohash(
        geohash: str,
        color: str = "blue",
        fill: bool = True,
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.5,
        weight: int = 2,
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
    ):
        """Add a geohash to the map.

        Args:
            geohash: Geohash string to add
            color: Color of the geohash border
            fill: Whether to fill the geohash
            fill_color: Color of the geohash fill (defaults to border color)
            fill_opacity: Opacity of the geohash fill
            weight: Width of the geohash border
            popup: Popup text (shown on click)
            tooltip: Tooltip text (shown on hover)
        """
        # Get bounding box for the geohash
        bbox = get_bounding_box(geohash)

        # Create rectangle
        folium.Rectangle(
            bounds=[[bbox.min_lat, bbox.min_lon], [bbox.max_lat, bbox.max_lon]],
            color=color,
            fill=fill,
            fill_color=fill_color or color,
            fill_opacity=fill_opacity,
            weight=weight,
            popup=popup or f"Geohash: {geohash}",
            tooltip=tooltip or f"Geohash: {geohash}",
        ).add_to(m)

        return m

    # Add method to add multiple geohashes
    def add_geohashes(
        geohashes: List[str],
        colors: Union[str, List[str]] = "blue",
        fill: bool = True,
        fill_colors: Optional[List[str]] = None,
        fill_opacity: float = 0.5,
        weight: int = 2,
        popups: Optional[List[str]] = None,
        tooltips: Optional[List[str]] = None,
    ):
        """Add multiple geohashes to the map.

        Args:
            geohashes: List of geohash strings to add
            colors: Color or list of colors for the geohash borders
            fill: Whether to fill the geohashes
            fill_colors: List of colors for the geohash fills (defaults to border colors)
            fill_opacity: Opacity of the geohash fills
            weight: Width of the geohash borders
            popups: List of popup texts (shown on click)
            tooltips: List of tooltip texts (shown on hover)
        """
        n_geohashes = len(geohashes)

        # Set up colors
        if isinstance(colors, str):
            colors = [colors] * n_geohashes
        elif len(colors) < n_geohashes:
            colors = colors * (n_geohashes // len(colors) + 1)
            colors = colors[:n_geohashes]

        # Set up fill colors
        if fill_colors is None:
            fill_colors = colors
        elif len(fill_colors) < n_geohashes:
            fill_colors = fill_colors * (n_geohashes // len(fill_colors) + 1)
            fill_colors = fill_colors[:n_geohashes]

        # Set up popups
        if popups is None:
            popups = [f"Geohash: {gh}" for gh in geohashes]
        elif len(popups) < n_geohashes:
            popups = list(popups) + [f"Geohash: {gh}" for gh in geohashes[len(popups) :]]

        # Set up tooltips
        if tooltips is None:
            tooltips = [f"Geohash: {gh}" for gh in geohashes]
        elif len(tooltips) < n_geohashes:
            tooltips = list(tooltips) + [f"Geohash: {gh}" for gh in geohashes[len(tooltips) :]]

        # Add each geohash
        for i, geohash in enumerate(geohashes):
            add_geohash(
                geohash,
                color=colors[i],
                fill=fill,
                fill_color=fill_colors[i],
                fill_opacity=fill_opacity,
                weight=weight,
                popup=popups[i],
                tooltip=tooltips[i],
            )

        return m

    # Add method to add a geohash grid
    def add_geohash_grid(
        precision: int = 6,
        bbox=None,
        color: str = "blue",
        fill: bool = True,
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.2,
        weight: int = 1,
    ):
        """Add a grid of geohashes at the specified precision.

        Args:
            precision: Precision of the geohashes
            bbox: Bounding box to limit the grid (min_lat, min_lon, max_lat, max_lon)
            color: Color of the geohash borders
            fill: Whether to fill the geohashes
            fill_color: Color of the geohash fills (defaults to border color)
            fill_opacity: Opacity of the geohash fills
            weight: Width of the geohash borders
        """

        # If no bounding box is provided, use the current map bounds
        if bbox is None:
            # This is an approximation based on the center and zoom level
            # For a more accurate approach, we would need to get the actual map bounds
            # which is not directly available in folium without JavaScript
            lat, lon = m.location
            # Rough estimate of degrees visible at different zoom levels
            # This is a very rough approximation
            degrees_visible = 360 / (2 ** (zoom_start - 1))
            bbox = (
                lat - degrees_visible / 2,
                lon - degrees_visible / 2,
                lat + degrees_visible / 2,
                lon + degrees_visible / 2,
            )

        # Get all geohashes in the bounding box
        bounding_box = BoundingBox(min_lat=bbox[0], min_lon=bbox[1], max_lat=bbox[2], max_lon=bbox[3])

        geohashes = geohashes_in_box(bounding_box, precision=precision)

        # Add geohashes to the map
        add_geohashes(
            geohashes,
            colors=color,
            fill=fill,
            fill_colors=fill_color or color,
            fill_opacity=fill_opacity,
            weight=weight,
        )

        return m

    # Attach methods to the map object
    m.add_geohash = add_geohash
    m.add_geohashes = add_geohashes
    m.add_geohash_grid = add_geohash_grid

    return m
