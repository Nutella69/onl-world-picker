@echo off
REM Build single-file Windows executable using PyInstaller
REM Install pyinstaller first: pip install pyinstaller

pyinstaller --onefile --noconsole main_gui.py
echo Build complete. Check the \dist folder for the executable.
