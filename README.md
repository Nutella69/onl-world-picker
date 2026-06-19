<<<<<<< HEAD
# onl-world-picker
Oxygen Not Included world trait reroll helper
=======
ONL World Picker — local helper

Purpose
- A simple Windows Python tool to help automate selecting worlds in Oxygen Not Included by screenshotting the world-traits area, OCRing text, and clicking the reroll button until desired traits appear.

Important
- Use only for local, single-player convenience. Do NOT use on multiplayer servers or in ways that violate Klei's Terms of Service.
- This tool mimics user clicks on your machine.

Requirements
- Windows
- Python 3.8+
- Tesseract OCR installed and added to PATH: https://github.com/tesseract-ocr/tesseract

Setup
1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install Tesseract and ensure `tesseract.exe` is on your PATH.

Usage
1. Start the game and open the world traits screen.
2. Run `python main.py` in a terminal.
3. Follow prompts to record the traits-area region and the reroll button coordinate by moving your mouse and pressing Enter.
4. Enter desired trait keywords (comma-separated). The script will loop: capture region -> OCR -> check keywords -> click reroll if not found.

Safety
- Press Ctrl+C in the terminal to stop the script immediately.
- Use conservative delays to avoid rapid clicking.
 - You can also press the `Esc` key (global hotkey) to stop the loop immediately while the script runs.

GUI version
- Run `python main_gui.py` to launch the Tkinter GUI. Use the buttons to record the traits region and reroll button, enter keywords and parameters, then press Start. Use Stop to halt.

Template / icon matching
- The GUI supports template/icon matching which is more reliable for non-text trait icons. Use "Add Template" to select one or more PNG/JPG images of the trait icon you want to detect. Set `Template threshold` (0.0-1.0, default 0.9) to tune sensitivity.
- Template images should be cropped to the icon and match the in-game scale. If your game resolution scales UI elements, capture templates at the same scale as the traits area.
- Template matches count towards the same stop `Mode` (e.g., `any` will stop if any keyword or any template matches).

Packaging as executable
- Install PyInstaller: `pip install pyinstaller`
- Run the included build script from the project folder:

```powershell
build_exe.bat
```

This creates a standalone executable in the `dist` folder. Note: you still need to install Tesseract on the target machine and ensure it's on PATH.

Share / Distribute
- Build the executable with `build_exe.bat`.
- Zip the resulting `dist\main_gui.exe` together with a copy of `README.md` and any template image files you want to include.
- Upload the zip to a file host or create a GitHub repository and publish it there.
- If you use GitHub, add a release and attach the zip/executable for users to download directly.
- Tell users to install Tesseract OCR before running the app and to use the GUI to set the trait region and reroll button.

Files
- `main.py`: main script
- `requirements.txt`: Python deps

>>>>>>> d5777dc (Initial commit for ONL World Picker)
