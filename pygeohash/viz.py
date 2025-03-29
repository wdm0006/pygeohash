"""Visualization module for PyGeoHash.

This module provides functions for visualizing geohashes on maps.
It requires additional dependencies that can be installed with:
    pip install pygeohash[viz]

Functions:
    plot_geohash: Plot a single geohash on a map
    plot_geohashes: Plot multiple geohashes on a map
    folium_map: Create an interactive map with geohashes using Folium
"""

# mypy: disable-error-code="list-item,assignment"

import warnings
from typing import List, Optional, Tuple, Union, Any, cast, TypeVar
from typing_extensions import TypeAlias, Protocol

from .geohash import decode
from .bounding_box import get_bounding_box, geohashes_in_box, BoundingBox

# Type aliases for better readability
FoliumMap: TypeAlias = Any  # Would be folium.Map if folium was always available
FoliumRectangle: TypeAlias = Any  # Would be folium.Rectangle if folium was always available
FoliumElement: TypeAlias = Any  # Would be folium.Element if folium was always available
MatplotlibAxis: TypeAlias = Any  # Would be matplotlib.axes.Axes if matplotlib was always available
MatplotlibFigure: TypeAlias = Any  # Would be matplotlib.figure.Figure if matplotlib was always available
BoundingBoxCoords = Tuple[float, float, float, float]  # min_lat, min_lon, max_lat, max_lon

T = TypeVar("T")


class FoliumMapProtocol(Protocol):
    """Protocol for Folium map objects."""

    location: Tuple[float, float]
    _zoom_start: int

    def add_child(self, child: FoliumElement, name: Optional[str] = None, index: Optional[int] = None) -> Any: ...

    def add_geohash(
        self,
        geohash: str,
        color: str = "blue",
        fill: bool = True,
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.5,
        weight: int = 2,
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> Any: ...

    def add_geohashes(
        self,
        geohashes: List[str],
        colors: Union[str, List[str]] = "blue",
        fill: bool = True,
        fill_colors: Optional[List[str]] = None,
        fill_opacity: float = 0.5,
        weight: int = 2,
        popups: Optional[List[str]] = None,
        tooltips: Optional[List[str]] = None,
    ) -> Any: ...

    def add_geohash_grid(
        self,
        precision: int = 6,
        bbox: Optional[BoundingBoxCoords] = None,
        color: str = "blue",
        fill: bool = True,
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.2,
        weight: int = 1,
    ) -> Any: ...


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
            "Matplotlib is required for visualization functions. Install with: pip install pygeohash[viz]", stacklevel=2
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
        warnings.warn("Folium is required for interactive maps. Install with: pip install pygeohash[viz]", stacklevel=2)
        return False


def plot_geohash(
    geohash: str,
    ax: Optional[MatplotlibAxis] = None,
    color: str = "blue",
    alpha: float = 0.5,
    label: Optional[str] = None,
    show_center: bool = False,
    show_label: bool = False,
    **kwargs: Any,
) -> Tuple[Optional[MatplotlibFigure], Optional[MatplotlibAxis]]:
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
    ax: Optional[MatplotlibAxis] = None,
    colors: Union[str, List[str]] = "viridis",
    alpha: float = 0.5,
    labels: Optional[List[str]] = None,
    show_centers: bool = False,
    show_labels: bool = False,
    **kwargs: Any,
) -> Tuple[Optional[MatplotlibFigure], Optional[MatplotlibAxis]]:
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
            colors_list = [cmap(i) for i in range(n_geohashes)]
        except ValueError:
            # If a single color name is provided
            colors_list = [colors] * n_geohashes
    elif len(colors) < n_geohashes:
        # If not enough colors are provided
        colors_list = colors * (n_geohashes // len(colors) + 1)
        colors_list = colors_list[:n_geohashes]
    else:
        colors_list = colors

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
            edgecolor=colors_list[i],
            facecolor=colors_list[i],
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


def add_geohash(
    self: FoliumMapProtocol,
    geohash: str,
    color: str = "blue",
    fill: bool = True,
    fill_color: Optional[str] = None,
    fill_opacity: float = 0.5,
    weight: int = 2,
    popup: Optional[str] = None,
    tooltip: Optional[str] = None,
) -> FoliumMapProtocol:
    """Add a geohash to the map."""
    import folium

    # Get bounding box for the geohash
    bbox = get_bounding_box(geohash)

    # Create rectangle
    rect = folium.Rectangle(
        bounds=[[bbox.min_lat, bbox.min_lon], [bbox.max_lat, bbox.max_lon]],
        color=color,
        fill=fill,
        fill_color=fill_color or color,
        fill_opacity=fill_opacity,
        weight=weight,
        popup=popup or f"Geohash: {geohash}",
        tooltip=tooltip or f"Geohash: {geohash}",
    )
    self.add_child(rect)

    return self


def add_geohashes(
    self: FoliumMapProtocol,
    geohashes: List[str],
    colors: Union[str, List[str]] = "blue",
    fill: bool = True,
    fill_colors: Optional[List[str]] = None,
    fill_opacity: float = 0.5,
    weight: int = 2,
    popups: Optional[List[str]] = None,
    tooltips: Optional[List[str]] = None,
) -> FoliumMapProtocol:
    """Add multiple geohashes to the map."""
    n_geohashes = len(geohashes)

    # Set up colors
    if isinstance(colors, str):
        colors_list = [colors] * n_geohashes
    elif len(colors) < n_geohashes:
        colors_list = list(colors) * (n_geohashes // len(colors) + 1)
        colors_list = colors_list[:n_geohashes]
    else:
        colors_list = list(colors)

    # Set up fill colors
    if fill_colors is None:
        fill_colors_list = colors_list
    elif len(fill_colors) < n_geohashes:
        fill_colors_list = list(fill_colors) * (n_geohashes // len(fill_colors) + 1)
        fill_colors_list = fill_colors_list[:n_geohashes]
    else:
        fill_colors_list = list(fill_colors)

    # Set up popups
    if popups is None:
        popups_list = [f"Geohash: {gh}" for gh in geohashes]
    elif len(popups) < n_geohashes:
        popups_list = list(popups) + [f"Geohash: {gh}" for gh in geohashes[len(popups) :]]
    else:
        popups_list = list(popups)

    # Set up tooltips
    if tooltips is None:
        tooltips_list = [f"Geohash: {gh}" for gh in geohashes]
    elif len(tooltips) < n_geohashes:
        tooltips_list = list(tooltips) + [f"Geohash: {gh}" for gh in geohashes[len(tooltips) :]]
    else:
        tooltips_list = list(tooltips)

    # Add each geohash
    for i, geohash in enumerate(geohashes):
        self.add_geohash(
            geohash,
            color=colors_list[i],
            fill=fill,
            fill_color=fill_colors_list[i],
            fill_opacity=fill_opacity,
            weight=weight,
            popup=popups_list[i],
            tooltip=tooltips_list[i],
        )

    return self


def add_geohash_grid(
    self: FoliumMapProtocol,
    precision: int = 6,
    bbox: Optional[BoundingBoxCoords] = None,
    color: str = "blue",
    fill: bool = True,
    fill_color: Optional[str] = None,
    fill_opacity: float = 0.2,
    weight: int = 1,
) -> FoliumMapProtocol:
    """Add a grid of geohashes at the specified precision."""
    # If no bounding box is provided, use the current map bounds
    if bbox is None:
        lat, lon = self.location
        # Rough estimate of degrees visible at different zoom levels
        degrees_visible = 360 / (2 ** (self._zoom_start - 1))
        bbox = (
            lat - degrees_visible / 2,  # min_lat
            lon - degrees_visible / 2,  # min_lon
            lat + degrees_visible / 2,  # max_lat
            lon + degrees_visible / 2,  # max_lon
        )

    # Get all geohashes in the bounding box
    min_lat, min_lon, max_lat, max_lon = bbox
    bounding_box = BoundingBox(min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon)
    geohashes = list(geohashes_in_box(bounding_box, precision=precision))

    # Add geohashes to the map
    self.add_geohashes(
        geohashes,
        colors=color,
        fill=fill,
        fill_colors=[fill_color] if fill_color else None,
        fill_opacity=fill_opacity,
        weight=weight,
    )

    return self


def folium_map(
    center_geohash: Optional[str] = None,
    center: Optional[Tuple[float, float]] = None,
    zoom_start: int = 13,
    tiles: str = "OpenStreetMap",
    width: str = "100%",
    height: str = "100%",
) -> Optional[FoliumMapProtocol]:
    """Create a folium map centered on a geohash or coordinates."""
    if not _check_folium_dependencies():
        return None

    import folium

    if center_geohash is not None:
        center = decode(center_geohash)

    if center is None:
        center = (0, 0)

    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles=tiles,
        width=width,
        height=height,
    )

    # Create a new class that inherits from the map's class and implements our protocol
    class GeohashMap(type(m), FoliumMapProtocol):  # type: ignore[misc]
        _zoom_start: int = zoom_start
        add_geohash = add_geohash
        add_geohashes = add_geohashes
        add_geohash_grid = add_geohash_grid

    # Convert the map instance to our new class
    m.__class__ = GeohashMap

    return cast(FoliumMapProtocol, m)
