import time
import pytesseract
from PIL import Image
import pyautogui
import cv2
import numpy as np
import threading
import re
import difflib
import winsound
try:
    import keyboard
except Exception:
    keyboard = None

print("ONL World Picker — interactive setup")
print("Make sure the game is visible and not full-screen (or use Alt+Tab to bring it up when prompted).\n")

# Helper to record mouse position when user presses Enter
def record_pos(prompt):
    input(f"{prompt}\nMove the mouse to position and press Enter...")
    pos = pyautogui.position()
    print(f"Recorded: {pos}")
    return pos

# Record region top-left and bottom-right
print("Step 1: Define the traits capture region.")
print("You will be asked to move the mouse to the TOP-LEFT corner of the traits area, then press Enter.")
top_left = record_pos("Top-left")
print("Now move the mouse to the BOTTOM-RIGHT corner of the traits area and press Enter.")
bottom_right = record_pos("Bottom-right")

x1, y1 = top_left
x2, y2 = bottom_right
w, h = x2 - x1, y2 - y1
if w <= 0 or h <= 0:
    print("Invalid region. Exiting.")
    exit(1)

print(f"Captured region: ({x1},{y1}) {w}x{h}")

# Record reroll button position
print('\nStep 2: Define the Reroll button position.')
reroll_pos = record_pos("Reroll button (click target)")

# Desired traits
raw = input("Enter desired trait keywords (comma-separated). Example: 'Gassy,Metal'\n> ")
keywords = [k.strip().lower() for k in raw.split(",") if k.strip()]
print(f"Looking for keywords: {keywords}")

# Matching mode: any (stop if any keyword), all (stop if all present), regex
mode = input("Matching mode - 'any' (default), 'all', or 'regex': ") or "any"
mode = mode.strip().lower()

# Fuzzy threshold for non-exact matches (0-1). Higher = stricter.
threshold = float(input("Fuzzy match threshold 0.0-1.0 (default 0.85): ") or 0.85)

# Optional tuning
delay_between_rerolls = float(input("Delay between rerolls in seconds (suggest 1.0): ") or 1.0)
ocr_lang = 'eng'  # adjust if needed

stop_event = threading.Event()

def on_hotkey():
    stop_event.set()

if keyboard:
    try:
        # global hotkey: Esc to stop
        keyboard.add_hotkey('esc', on_hotkey)
        print("Press Esc to stop the loop (global hotkey).")
    except Exception:
        print("Warning: could not register global hotkey. You can still use Ctrl+C.")
else:
    print("Tip: install 'keyboard' package to enable a global hotkey (Esc) to stop.")

print("Starting loop. Press Ctrl+C or Esc to stop.")
try:
    while not stop_event.is_set():
        # capture
        img = pyautogui.screenshot(region=(x1, y1, w, h))
        # Convert to grayscale numpy array for optional preprocessing
        arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        # basic threshold to improve OCR
        _,th = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        pil = Image.fromarray(th)
        text = pytesseract.image_to_string(pil, lang=ocr_lang)
        text_low = text.lower()
        print("OCR text snippet:", repr(text_low[:200]))

        # Tokenize for fuzzy matching
        tokens = re.findall(r"\w+", text_low)
        found_keywords = set()

        if mode == 'regex':
            for kw in keywords:
                try:
                    if re.search(kw, text_low):
                        found_keywords.add(kw)
                except re.error:
                    # treat as literal if invalid regex
                    if kw in text_low:
                        found_keywords.add(kw)
        else:
            for kw in keywords:
                if kw in text_low:
                    found_keywords.add(kw)
                    continue
                # fuzzy match against tokens
                for tok in tokens:
                    if difflib.SequenceMatcher(None, kw, tok).ratio() >= threshold:
                        found_keywords.add(kw)
                        break

        # Evaluate stop condition
        if mode == 'all' and len(found_keywords) == len(keywords) and len(keywords) > 0:
            print(f"All keywords found: {found_keywords} — stopping.")
            winsound.Beep(1000, 300)
            break
        if mode == 'any' and len(found_keywords) > 0:
            print(f"Found keyword(s): {found_keywords} — stopping.")
            winsound.Beep(1000, 300)
            break

        # Click reroll
        rx, ry = reroll_pos
        pyautogui.click(rx, ry)
        time.sleep(delay_between_rerolls)
except KeyboardInterrupt:
    print("Stopped by user.")

print("Done.")
