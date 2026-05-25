from pathlib import Path

from lxml import etree

from converter import obj_to_landxml

NS = {"lx": "http://www.landxml.org/schema/LandXML-1.2"}


def test_obj_to_landxml_coordinate_swap_and_counts(tmp_path: Path) -> None:
    input_path = Path(__file__).parent / "sample_data" / "sample.obj"
    output_path = tmp_path / "output.xml"

    result = obj_to_landxml.convert(str(input_path), str(output_path))
    tree = etree.parse(str(output_path))

    assert result["total_vertices"] == 3
    assert result["total_faces"] == 1
    assert tree.getroot().get("version") == "1.2"
    assert tree.xpath("string(//lx:Surface/@name)", namespaces=NS) == "現況地形"
    points = tree.xpath("//lx:P/text()", namespaces=NS)
    assert points == [
        "35000.000000 135000.000000 50.000000",
        "35001.000000 135001.000000 51.000000",
        "35002.000000 135000.500000 49.500000",
    ]
    assert tree.xpath("//lx:F/text()", namespaces=NS) == ["1 2 3"]


def test_obj_to_landxml_parses_supported_face_forms(tmp_path: Path) -> None:
    input_path = tmp_path / "faces.obj"
    output_path = tmp_path / "faces.xml"
    input_path.write_text(
        """o Forms
v 1 2 3
v 4 5 6
v 7 8 9
v 10 11 12
f 1 2 3
f 1/1 2/2 3/3
f 1/1/1 2/2/2 3/3/3
f 1//1 2//2 3//3
f 1 2 3 4
""",
        encoding="utf-8",
    )

    result = obj_to_landxml.convert(str(input_path), str(output_path))
    tree = etree.parse(str(output_path))
    faces = tree.xpath("//lx:F/text()", namespaces=NS)

    assert result["total_faces"] == 6
    assert faces[:4] == ["1 2 3", "1 2 3", "1 2 3", "1 2 3"]
    assert faces[-2:] == ["1 2 3", "1 3 4"]
