"""Coordinate conversion helpers for GeoMesh Converter."""

from __future__ import annotations


def swap_xy(x: float, y: float, z: float) -> tuple[float, float, float]:
    """Return a coordinate tuple with X and Y swapped."""
    return (y, x, z)
