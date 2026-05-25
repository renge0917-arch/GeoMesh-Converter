GeoMesh Converter v1.0 - Windows exe build guide
=================================================

Run build_windows.bat inside the extracted geomesh_converter folder.

Requirements:
- Windows PC
- Python 3.10 or later
- Internet connection for the first dependency download

Steps:
1. Extract the zip file first. Do not run the bat file directly from inside the zip viewer.
2. Open the extracted geomesh_converter folder.
3. Double-click build_windows.bat.
4. When finished, GeoMeshConverter.exe will be created in the dist folder.
5. Double-click dist\GeoMeshConverter.exe to use the app.

If the window closes or an error appears:
- The script writes build_log.txt in this folder.
- Open build_log.txt and check the last lines.
- You can also run it from Command Prompt:

  cd /d C:\path\to\geomesh_converter
  build_windows.bat

Common causes:
- The zip was not extracted before running the script.
- Python is not installed.
- Python was installed without "Add python.exe to PATH" enabled.
- pip install is blocked by network/proxy/security software.

Note:
The Genspark sandbox is Linux, so a real Windows .exe must be built on Windows.
This build_windows.bat automates that Windows-side build.
