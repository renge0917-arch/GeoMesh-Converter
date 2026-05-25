"""Normal vector calculation utilities for OBJ export."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

Vector3 = tuple[float, float, float]
Face = tuple[int, int, int]


def calc_face_normal(v1: Iterable[float], v2: Iterable[float], v3: Iterable[float]) -> np.ndarray:
    """Calculate a normalized triangle face normal using the cross product."""
    edge1 = np.array(tuple(v2), dtype=float) - np.array(tuple(v1), dtype=float)
    edge2 = np.array(tuple(v3), dtype=float) - np.array(tuple(v1), dtype=float)
    normal = np.cross(edge1, edge2)
    length = np.linalg.norm(normal)
    if length == 0:
        return np.array([0.0, 0.0, 1.0], dtype=float)
    return normal / length


def calc_vertex_normals(vertices: dict[int, Vector3], faces: list[Face]) -> dict[int, Vector3]:
    """Calculate area-weighted averaged vertex normals for shared triangle faces."""
    accumulators: dict[int, np.ndarray] = {
        vertex_id: np.array([0.0, 0.0, 0.0], dtype=float) for vertex_id in vertices
    }

    for face in faces:
        try:
            v1, v2, v3 = (np.array(vertices[vertex_id], dtype=float) for vertex_id in face)
        except KeyError:
            continue

        weighted_normal = np.cross(v2 - v1, v3 - v1)
        if np.linalg.norm(weighted_normal) == 0:
            weighted_normal = np.array([0.0, 0.0, 1.0], dtype=float)
        for vertex_id in face:
            accumulators[vertex_id] += weighted_normal

    normals: dict[int, Vector3] = {}
    for vertex_id, normal in accumulators.items():
        length = np.linalg.norm(normal)
        if length == 0:
            normals[vertex_id] = (0.0, 0.0, 1.0)
        else:
            normalized = normal / length
            normals[vertex_id] = tuple(float(value) for value in normalized)
    return normals
