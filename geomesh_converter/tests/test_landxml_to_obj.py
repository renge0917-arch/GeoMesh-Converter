from pathlib import Path

from converter import landxml_to_obj


def test_landxml_to_obj_coordinate_swap_and_counts(tmp_path: Path) -> None:
    input_path = Path(__file__).parent / "sample_data" / "sample.xml"
    output_path = tmp_path / "output.obj"

    result = landxml_to_obj.convert(str(input_path), str(output_path))
    content = output_path.read_text(encoding="utf-8")

    assert result["total_vertices"] == 3
    assert result["total_faces"] == 1
    assert "o 現況地形" in content
    assert "v 135000.000000 35000.000000 50.000000" in content
    assert "v 135001.000000 35001.000000 51.000000" in content
    assert "v 135000.500000 35002.000000 49.500000" in content
    assert "f 1//1 2//2 3//3" in content


def test_landxml_to_obj_skips_invisible_and_missing_faces(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid_faces.xml"
    output_path = tmp_path / "output.obj"
    input_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<LandXML version="1.2">
  <Surfaces><Surface name="S"><Definition surfType="TIN">
    <Pnts><P id="10">1 2 3</P><P id="20">4 5 6</P><P id="30">7 8 9</P></Pnts>
    <Faces><F i="1">10 20 30</F><F>10 20 999</F><F>10 20 30</F></Faces>
  </Definition></Surface></Surfaces>
</LandXML>
""",
        encoding="utf-8",
    )

    result = landxml_to_obj.convert(str(input_path), str(output_path))

    assert result["total_faces"] == 1
    assert result["warnings"]
    assert "f 1//1 2//2 3//3" in output_path.read_text(encoding="utf-8")
