"""OBJ to LandXML TIN surface conversion."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from lxml import etree

from .coord_swap import swap_xy

LANDXML_NS = "http://www.landxml.org/schema/LandXML-1.2"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

Vector3 = tuple[float, float, float]
Face = tuple[int, int, int]


@dataclass
class ObjSurface:
    name: str
    vertex_indices: list[int] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)


def _parse_face_vertex(token: str, vertex_count: int) -> int:
    index_text = token.split("/", 1)[0]
    if not index_text:
        raise ValueError("頂点インデックスが空です")
    index = int(index_text)
    if index < 0:
        index = vertex_count + index + 1
    if index <= 0 or index > vertex_count:
        raise ValueError(f"頂点インデックス {index} が範囲外です")
    return index


def _triangulate(indices: list[int]) -> list[Face]:
    if len(indices) < 3:
        return []
    return [(indices[0], indices[index], indices[index + 1]) for index in range(1, len(indices) - 1)]


def _parse_obj(input_path: str) -> tuple[list[Vector3], list[ObjSurface], list[str]]:
    vertices: list[Vector3] = []
    surfaces: list[ObjSurface] = []
    warnings: list[str] = []
    current = ObjSurface(name="Surface")
    surfaces.append(current)

    with open(input_path, "r", encoding="utf-8-sig") as obj_file:
        for line_number, raw_line in enumerate(obj_file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            command = parts[0]

            if command == "o":
                name = line[2:].strip() or f"Surface{len(surfaces) + 1}"
                if current.vertex_indices or current.faces:
                    current = ObjSurface(name=name)
                    surfaces.append(current)
                else:
                    current.name = name
            elif command == "v":
                if len(parts) < 4:
                    warnings.append(f"行{line_number}: 頂点データの形式が不正です")
                    continue
                try:
                    vertex = (float(parts[1]), float(parts[2]), float(parts[3]))
                except ValueError:
                    warnings.append(f"行{line_number}: 頂点データの形式が不正です")
                    continue
                vertices.append(vertex)
                current.vertex_indices.append(len(vertices))
            elif command == "f":
                try:
                    indices = [_parse_face_vertex(token, len(vertices)) for token in parts[1:]]
                except ValueError as exc:
                    warnings.append(f"行{line_number}: フェイスデータの形式が不正です: {exc}")
                    continue
                faces = _triangulate(indices)
                if not faces:
                    warnings.append(f"行{line_number}: フェイスデータの形式が不正です")
                    continue
                current.faces.extend(faces)

    return vertices, [surface for surface in surfaces if surface.vertex_indices or surface.faces], warnings


def _build_landxml(vertices: list[Vector3], surfaces: list[ObjSurface]) -> etree._ElementTree:
    now = datetime.now()
    nsmap = {None: LANDXML_NS, "xsi": XSI_NS}
    root = etree.Element(
        f"{{{LANDXML_NS}}}LandXML",
        nsmap=nsmap,
        version="1.2",
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
    )
    etree.SubElement(root, f"{{{LANDXML_NS}}}Project", name="GeoMesh Converter Output")
    etree.SubElement(
        root,
        f"{{{LANDXML_NS}}}Application",
        name="GeoMesh Converter",
        version="1.0",
        manufacturer="ICT推進課",
    )
    surfaces_element = etree.SubElement(root, f"{{{LANDXML_NS}}}Surfaces")

    for surface in surfaces:
        surface_element = etree.SubElement(surfaces_element, f"{{{LANDXML_NS}}}Surface", name=surface.name)
        definition = etree.SubElement(surface_element, f"{{{LANDXML_NS}}}Definition", surfType="TIN")
        pnts = etree.SubElement(definition, f"{{{LANDXML_NS}}}Pnts")
        local_id_map = {global_id: local_id for local_id, global_id in enumerate(surface.vertex_indices, start=1)}
        for global_id in surface.vertex_indices:
            northing, easting, elevation = swap_xy(*vertices[global_id - 1])
            point = etree.SubElement(pnts, f"{{{LANDXML_NS}}}P", id=str(local_id_map[global_id]))
            point.text = f"{northing:.6f} {easting:.6f} {elevation:.6f}"

        faces = etree.SubElement(definition, f"{{{LANDXML_NS}}}Faces")
        for face in surface.faces:
            if not all(vertex_id in local_id_map for vertex_id in face):
                continue
            face_element = etree.SubElement(faces, f"{{{LANDXML_NS}}}F")
            face_element.text = " ".join(str(local_id_map[vertex_id]) for vertex_id in face)

    return etree.ElementTree(root)


def convert(input_path: str, output_path: str) -> dict:
    """Convert an OBJ file to a LandXML 1.2 TIN surface file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError("入力ファイルが見つかりません")

    vertices, surfaces, warnings = _parse_obj(input_path)
    if not vertices:
        raise ValueError("OBJに頂点データが見つかりません")
    if not surfaces:
        raise ValueError("OBJに変換対象オブジェクトが見つかりません")

    tree = _build_landxml(vertices, surfaces)
    try:
        tree.write(output_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    except OSError as exc:
        raise OSError("ファイルの書き込みに失敗しました。出力先を確認してください") from exc

    surface_summary = []
    for surface in surfaces:
        surface_summary.append(
            {"name": surface.name, "vertices": len(surface.vertex_indices), "faces": len(surface.faces)}
        )

    return {
        "surfaces": surface_summary,
        "total_vertices": sum(item["vertices"] for item in surface_summary),
        "total_faces": sum(item["faces"] for item in surface_summary),
        "warnings": warnings,
    }
