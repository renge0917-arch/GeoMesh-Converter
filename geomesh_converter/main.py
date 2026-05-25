"""GeoMesh Converter application entry point."""

from __future__ import annotations

from gui import GeoMeshConverterApp


def main() -> None:
    """Start the GeoMesh Converter GUI."""
    app = GeoMeshConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
