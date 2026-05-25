"""LandXML TIN surface to OBJ conversion."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from .coord_swap import swap_xy
from .normal_calc import calc_vertex_normals

LANDXML_NAMESPACES = (
    "http://www.landxml.org/schema/LandXML-1.0",
    "http://www.landxml.org/schema/LandXML-1.1",
    "http://www.landxml.org/schema/LandXML-1.2",
)

Vector3 = tuple[float, float, float]
Face = tuple[int, int, int]


@dataclass
class SurfaceData:
    name: str
    vertices: dict[int, Vector3] = field(default_factory=dict)
    faces: list[Face] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def _iter_children(element: etree._Element, name: str) -> list[etree._Element]:
    return [child for child in element if _local_name(child) == name]


def _first_child(element: etree._Element, name: str) -> etree._Element | None:
    for child in element:
        if _local_name(child) == name:
            return child
    return None


def _find_tin_surfaces(root: etree._Element) -> list[tuple[etree._Element, etree._Element]]:
    surfaces_parent = next((el for el in root.iter() if _local_name(el) == "Surfaces"), None)
    if surfaces_parent is None:
        return []

    result: list[tuple[etree._Element, etree._Element]] = []
    for surface in _iter_children(surfaces_parent, "Surface"):
        definition = _first_child(surface, "Definition")
        if definition is not None and definition.get("surfType") == "TIN":
            result.append((surface, definition))
    return result


def _parse_point(point: etree._Element) -> tuple[int, Vector3]:
    point_id_raw = point.get("id")
    if point_id_raw is None:
        raise ValueError("ポイントIDがありません")
    point_id = int(point_id_raw)
    values = (point.text or "").split()
    if len(values) < 3:
        raise ValueError("座標値が3つありません")
    northing, easting, elevation = (float(values[index]) for index in range(3))
    return point_id, (northing, easting, elevation)


def _parse_face(face: etree._Element) -> Face:
    values = (face.text or "").split()
    if len(values) < 3:
        raise ValueError("フェイス頂点IDが3つありません")
    return tuple(int(values[index]) for index in range(3))  # type: ignore[return-value]


def _parse_surface(surface: etree._Element, definition: etree._Element) -> SurfaceData:
    surface_name = surface.get("name") or "Surface"
    data = SurfaceData(name=surface_name)
    pnts = _first_child(definition, "Pnts")
    faces = _first_child(definition, "Faces")
    if pnts is None or faces is None:
        data.warnings.append(f"Surface '{surface_name}': PntsまたはFacesが見つかりません")
        return data

    for point in _iter_children(pnts, "P"):
        point_id_label = point.get("id") or "不明"
        try:
            point_id, coordinates = _parse_point(point)
        except ValueError as exc:
            data.warnings.append(f"ポイントID:{point_id_label}の座標値が不正です: {exc}")
            continue
        data.vertices[point_id] = coordinates

    for face in _iter_children(faces, "F"):
        if face.get("i") == "1":
            continue
        try:
            parsed_face = _parse_face(face)
        except ValueError as exc:
            data.warnings.append(f"フェイスデータが不正です: {exc}")
            continue
        missing_ids = [vertex_id for vertex_id in parsed_face if vertex_id not in data.vertices]
        if missing_ids:
            data.warnings.append(
                "フェイスが参照するポイントID:"
                + ",".join(str(vertex_id) for vertex_id in missing_ids)
                + "が存在しません"
            )
            continue
        data.faces.append(parsed_face)

    return data


def _format_obj_surface(surface: SurfaceData, vertex_offset: int) -> tuple[list[str], int]:
    if not surface.vertices:
        return [f"o {surface.name}"], 0

    sorted_ids = sorted(surface.vertices)
    id_map = {original_id: index + 1 + vertex_offset for index, original_id in enumerate(sorted_ids)}
    local_vertices = {
        id_map[original_id]: swap_xy(*surface.vertices[original_id]) for original_id in sorted_ids
    }
    local_faces = [tuple(id_map[vertex_id] for vertex_id in face) for face in surface.faces]
    normals = calc_vertex_normals(local_vertices, local_faces)

    lines = [f"o {surface.name}"]
    for vertex_id in sorted(local_vertices):
        x, y, z = local_vertices[vertex_id]
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for vertex_id in sorted(local_vertices):
        nx, ny, nz = normals[vertex_id]
        lines.append(f"vn {nx:.6f} {ny:.6f} {nz:.6f}")
    for face in local_faces:
        lines.append("f " + " ".join(f"{vertex_id}//{vertex_id}" for vertex_id in face))
    return lines, len(local_vertices)


def convert(input_path: str, output_path: str) -> dict:
    """Convert a LandXML TIN surface file to an OBJ file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError("入力ファイルが見つかりません")

    try:
        tree = etree.parse(input_path)
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"LandXMLの読み込みに失敗しました: {exc}") from exc

    root = tree.getroot()
    namespace = etree.QName(root).namespace
    if namespace not in LANDXML_NAMESPACES and namespace is not None:
        # Unknown namespaces may still be structurally compatible; continue by local-name parsing.
        pass

    tin_surfaces = _find_tin_surfaces(root)
    if not tin_surfaces:
        raise ValueError("TINサーフェスが見つかりません")

    surfaces = [_parse_surface(surface, definition) for surface, definition in tin_surfaces]
    total_vertices = sum(len(surface.vertices) for surface in surfaces)
    total_faces = sum(len(surface.faces) for surface in surfaces)
    warnings = [warning for surface in surfaces for warning in surface.warnings]

    lines = ["# GeoMesh Converter v1.0"]
    if surfaces:
        lines.append("# Source: " + ", ".join(surface.name for surface in surfaces))

    vertex_offset = 0
    for surface in surfaces:
        surface_lines, vertex_count = _format_obj_surface(surface, vertex_offset)
        lines.extend(surface_lines)
        vertex_offset += vertex_count

    try:
        Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        raise OSError("ファイルの書き込みに失敗しました。出力先を確認してください") from exc

    return {
        "surfaces": [
            {"name": surface.name, "vertices": len(surface.vertices), "faces": len(surface.faces)}
            for surface in surfaces
        ],
        "total_vertices": total_vertices,
        "total_faces": total_faces,
        "warnings": warnings,
    }
