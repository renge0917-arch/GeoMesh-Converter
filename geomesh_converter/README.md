# GeoMesh Converter

GeoMesh Converter v1.0 is a local Python desktop application that converts construction ICT LandXML TIN surfaces to Blender OBJ files and converts edited OBJ files back to LandXML 1.2.

## Supported conversions

- LandXML → OBJ
- OBJ → LandXML

LandXML point coordinates are stored as `Northing Easting Elevation`; OBJ vertices are emitted as `Easting Northing Elevation`. The reverse conversion writes OBJ `X Y Z` as LandXML `Y X Z`.

## Setup

```bash
pip install -r requirements.txt
```

## Run GUI

```bash
python main.py
```

## Build Windows exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name GeoMeshConverter main.py
```

The executable is output to `dist/GeoMeshConverter.exe`.
