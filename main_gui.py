import threading
import time
import re
import difflib
from tkinter import filedialog, colorchooser
import tkinter as tk
from tkinter import ttk, messagebox
import pytesseract
from PIL import Image
import pyautogui
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False
import cv2
import numpy as np
import winsound
import ctypes
import shutil
import os
try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except Exception:
    mouse = None
    PYNPUT_AVAILABLE = False
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except Exception:
    KEYBOARD_AVAILABLE = False


class WorldPickerGUI:
    VALID_TRAITS = [
        'large boulders',
        'medium boulders',
        'small boulders',
        'mixed boulders',
        'buried oil',
        'frozen core',
        'geoactive',
        'geodormant',
        'geodes',
        'large glaciers',
        'irregular oil',
        'magma channels',
        'metal poor',
        'metal rich',
        'alternate pod location',
        'slime molds',
        'subsurface ocean',
        'trapped oil',
        'volcanoes',
        'crashed satellite',
        'frozen friend',
        'lush core',
        'metallic caves',
        'radioactive crust'
    ]

    def __init__(self, root):
        # Try to make coordinates DPI-aware on Windows so clicks/screenshot coords match
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

        self.root = root
        root.title('ONL World Picker')

        frm = ttk.Frame(root, padding=10)
        frm.grid()

        ttk.Label(frm, text='Traits region:').grid(column=0, row=0, sticky='w')
        self.region_var = tk.StringVar(value='Not set')
        ttk.Label(frm, textvariable=self.region_var).grid(column=1, row=0, sticky='w')
        ttk.Button(frm, text='Record Region', command=self.record_region).grid(column=2, row=0)

        ttk.Label(frm, text='Reroll button:').grid(column=0, row=1, sticky='w')
        self.reroll_var = tk.StringVar(value='Not set')
        ttk.Label(frm, textvariable=self.reroll_var).grid(column=1, row=1, sticky='w')
        ttk.Button(frm, text='Record Reroll', command=self.record_reroll).grid(column=2, row=1)

        self.style = ttk.Style()
        self.style.theme_use('default')
        self.theme_color = '#333333'
        self.style.configure('Custom.TFrame', background=self.theme_color)
        self.style.configure('TLabel', background=self.theme_color, foreground='#ffffff')
        self.style.configure('TButton', background='#444444', foreground='#ffffff')
        self.style.configure('TEntry', fieldbackground='#ffffff')
        root.configure(bg=self.theme_color)
        frm.configure(style='Custom.TFrame')

        ttk.Label(frm, text='Trait count:').grid(column=0, row=2, sticky='w')
        self.trait_count_cb = ttk.Combobox(frm, values=['1', '2', '3', '4'], width=5, state='readonly')
        self.trait_count_cb.set('1')
        self.trait_count_cb.grid(column=1, row=2, sticky='w')
        self.trait_count_cb.bind('<<ComboboxSelected>>', self.on_trait_count_change)

        ttk.Label(frm, text='Choose exact traits:').grid(column=0, row=3, sticky='w')
        self.trait_listbox = tk.Listbox(frm, selectmode='multiple', height=10, width=50, exportselection=False)
        self.trait_listbox.grid(column=0, row=4, columnspan=3, sticky='w')
        self.trait_listbox.bind('<<ListboxSelect>>', self.on_trait_selection_change)
        for trait in self.VALID_TRAITS:
            self.trait_listbox.insert('end', trait)
        self.trait_limit_label = ttk.Label(frm, text='Select exactly 4 traits.')
        self.trait_limit_label.grid(column=0, row=5, columnspan=3, sticky='w')
        self.selected_traits_var = tk.StringVar(value='Selected: none')
        ttk.Label(frm, textvariable=self.selected_traits_var).grid(column=0, row=6, columnspan=3, sticky='w')

        ttk.Label(frm, text='Fuzzy threshold:').grid(column=0, row=7, sticky='w')
        self.threshold_entry = ttk.Entry(frm, width=10)
        self.threshold_entry.insert(0, '0.85')
        self.threshold_entry.grid(column=1, row=7, sticky='w')

        ttk.Label(frm, text='Delay (s):').grid(column=0, row=7, sticky='w')
        self.delay_entry = ttk.Entry(frm, width=10)
        self.delay_entry.insert(0, '1.0')
        self.delay_entry.grid(column=1, row=7, sticky='w')

        ttk.Label(frm, text='Tesseract path:').grid(column=0, row=8, sticky='w')
        self.tesseract_path_var = tk.StringVar()
        self.tesseract_entry = ttk.Entry(frm, width=40, textvariable=self.tesseract_path_var)
        self.tesseract_entry.grid(column=1, row=8, sticky='w')
        ttk.Button(frm, text='Browse', command=self.browse_tesseract).grid(column=2, row=8, sticky='w')

        ttk.Button(frm, text='Pick theme color', command=self.pick_color).grid(column=0, row=9, sticky='w')
        self.color_preview = tk.Label(frm, text='      ', bg=self.theme_color)
        self.color_preview.grid(column=1, row=9, sticky='w')

        self.start_btn = ttk.Button(frm, text='Start', command=self.start)
        self.start_btn.grid(column=0, row=10)
        self.stop_btn = ttk.Button(frm, text='Stop', command=self.stop, state='disabled')
        self.stop_btn.grid(column=1, row=10)
        self.hotkey_label = ttk.Label(frm, text='Hotkey: F8 to toggle start/stop')
        self.hotkey_label.grid(column=2, row=10, sticky='w')

        self.capture_status_var = tk.StringVar(value='Capture mode: none')
        ttk.Label(frm, textvariable=self.capture_status_var).grid(column=0, row=11, columnspan=3, sticky='w')

        ttk.Label(frm, text='Status:').grid(column=0, row=12, sticky='nw')
        self.status_txt = tk.Text(frm, width=60, height=12)
        self.status_txt.grid(column=0, row=13, columnspan=3)

        self.worker = None
        self.stop_event = threading.Event()
        self.region = None
        self.reroll = None
        self.capture_mode = None
        self.capture_listener = None
        self._region_points = []
        self.update_trait_selection_limit()

        self.detect_tesseract()

        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey('F8', lambda: root.after(0, self.toggle_start_stop))
                self.log('Hotkey F8 registered (toggle start/stop)')
            except Exception as e:
                self.log('Hotkey registration failed:', e)

    def toggle_start_stop(self):
        if self.worker and self.worker.is_alive():
            self.stop()
        else:
            self.start()

    def detect_tesseract(self):
        path = shutil.which('tesseract')
        if path:
            self.tesseract_path_var.set(path)
        elif os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
            self.tesseract_path_var.set(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        elif os.path.exists(r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'):
            self.tesseract_path_var.set(r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe')

    def browse_tesseract(self):
        path = filedialog.askopenfilename(title='Select tesseract.exe', filetypes=[('Executable files', '*.exe')])
        if path:
            self.tesseract_path_var.set(path)

    def log(self, *args):
        self.status_txt.insert('end', ' '.join(str(a) for a in args) + '\n')
        self.status_txt.see('end')

    def record_region(self):
        if not PYNPUT_AVAILABLE:
            messagebox.showerror('Missing dependency', 'Left-click capture requires pynput. Install it with pip install pynput in the venv.')
            return
        self.stop_capture()
        self.capture_mode = 'region'
        self._region_points = []
        self.capture_status_var.set('Capture mode: region (click top-left, then bottom-right)')
        self.log('Region recording active. Click top-left, then click bottom-right.')
        self.start_capture_listener()

    def record_reroll(self):
        if not PYNPUT_AVAILABLE:
            messagebox.showerror('Missing dependency', 'Left-click capture requires pynput. Install it with pip install pynput in the venv.')
            return
        self.stop_capture()
        self.capture_mode = 'reroll'
        self.capture_status_var.set('Capture mode: reroll (click reroll button)')
        self.log('Ready to capture reroll with left-click.')
        self.start_capture_listener()

    def start_capture_listener(self):
        if self.capture_listener is not None:
            return
        self.capture_listener = mouse.Listener(on_click=self._on_capture_click)
        self.capture_listener.daemon = True
        self.capture_listener.start()

    def stop_capture(self):
        if self.capture_listener:
            try:
                self.capture_listener.stop()
            except Exception:
                pass
            self.capture_listener = None
        self.capture_mode = None
        self._region_points = []
        self.capture_status_var.set('Capture mode: none')

    def _on_capture_click(self, x, y, button, pressed):
        if pressed or button != mouse.Button.left:
            return
        if self.capture_mode == 'region':
            self._region_points.append((x, y))
            if len(self._region_points) == 1:
                self.root.after(0, lambda: self.log('Top-left captured at', x, y))
                self.root.after(0, lambda: self.capture_status_var.set('Capture mode: region (click bottom-right)'))
                return
            if len(self._region_points) == 2:
                x1, y1 = self._region_points[0]
                x2, y2 = self._region_points[1]
                w, h = x2 - x1, y2 - y1
                if w <= 0 or h <= 0:
                    self.root.after(0, lambda: self.log('Invalid region captured. Please try again.'))
                    self.stop_capture()
                    return
                self.region = (x1, y1, w, h)
                self.root.after(0, lambda: self.region_var.set(f'{x1},{y1} {w}x{h}'))
                self.root.after(0, lambda: self.log('Region set:', self.region))
                self.stop_capture()
        elif self.capture_mode == 'reroll':
            self.reroll = (x, y)
            self.root.after(0, lambda: self.reroll_var.set(f'{x},{y}'))
            self.root.after(0, lambda: self.log('Reroll set:', self.reroll))
            self.stop_capture()

    def on_trait_count_change(self, event=None):
        self.update_trait_selection_limit()

    def update_trait_selection_limit(self):
        count = int(self.trait_count_cb.get())
        self.trait_limit_label.config(text=f'Select exactly {count} trait(s).')
        selected = list(self.trait_listbox.curselection())
        if len(selected) > count:
            for idx in selected[count:]:
                self.trait_listbox.selection_clear(idx)
        self.on_trait_selection_change()

    def pick_color(self):
        color_code = colorchooser.askcolor(title='Pick theme color', initialcolor=self.theme_color)
        if color_code and color_code[1]:
            self.theme_color = color_code[1]
            self.color_preview.config(bg=self.theme_color)
            self.root.configure(bg=self.theme_color)
            self.style.configure('Custom.TFrame', background=self.theme_color)
            self.style.configure('TLabel', background=self.theme_color)

    def on_trait_selection_change(self, event=None):
        count = int(self.trait_count_cb.get())
        selected_indices = list(self.trait_listbox.curselection())
        if len(selected_indices) > count:
            for idx in selected_indices[count:]:
                self.trait_listbox.selection_clear(idx)
            selected_indices = list(self.trait_listbox.curselection())
        if selected_indices:
            selected_traits = [self.VALID_TRAITS[i] for i in selected_indices]
            self.selected_traits_var.set('Selected: ' + ', '.join(selected_traits))
        else:
            self.selected_traits_var.set('Selected: none')

    def start(self):
        if not self.region or not self.reroll:
            messagebox.showerror('Error', 'Region and reroll must be set first.')
            return

        count = int(self.trait_count_cb.get())
        selected_indices = self.trait_listbox.curselection()
        if len(selected_indices) != count:
            messagebox.showerror('Error', f'Please select exactly {count} traits.')
            return

        kws = [self.VALID_TRAITS[i] for i in selected_indices]
        try:
            threshold = float(self.threshold_entry.get())
        except Exception:
            threshold = 0.85
        try:
            delay = float(self.delay_entry.get())
        except Exception:
            delay = 1.0

        tesseract_path = self.tesseract_path_var.get().strip()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        params = {
            'region': self.region,
            'reroll': self.reroll,
            'keywords': kws,
            'mode': 'all',
            'threshold': threshold,
            'delay': delay,
        }
        self.stop_event.clear()
        self.worker = threading.Thread(target=self.loop_worker, args=(params,))
        self.worker.start()
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.log('Started. All selected traits are required before stopping.')

    def stop(self):
        self.stop_event.set()
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.log('Stopping...')

    def loop_worker(self, params):
        region = params['region']
        reroll = params['reroll']
        keywords = params['keywords']
        mode = params['mode']
        threshold = params['threshold']
        delay = params['delay']

        while not self.stop_event.is_set():
            img = pyautogui.screenshot(region=region)
            arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
            _, th = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            pil = Image.fromarray(th)
            try:
                text = pytesseract.image_to_string(pil, lang='eng')
            except pytesseract.pytesseract.TesseractNotFoundError:
                self.log('ERROR: Tesseract not found. Please install it or set the path.')
                messagebox.showerror('Tesseract not found', 'Tesseract OCR executable was not found. Install it or provide the path.')
                self.stop_event.set()
                break
            except Exception as e:
                self.log('OCR error:', e)
                self.stop_event.set()
                break
            text_low = text.lower()
            self.log('OCR:', text_low[:200])

            found = set()

            detected_traits = [trait for trait in self.VALID_TRAITS if trait in text_low]
            self.log('Detected trait candidates in OCR:', detected_traits)

            for kw in keywords:
                # avoid false positives by only matching against the known trait list
                if kw in detected_traits:
                    found.add(kw)
                else:
                    for trait in detected_traits:
                        if difflib.SequenceMatcher(None, kw, trait).ratio() >= threshold:
                            found.add(kw)
                            break

            # Debugging: show which keywords were found vs required
            missing = [kw for kw in keywords if kw not in found]
            if missing:
                self.log('Missing keywords:', missing)
            else:
                self.log('All required keywords detected (pre-template check).')

            # If mode == 'all', require that every specified keyword was found
            if mode == 'all' and len(keywords) > 0:
                # ensure all keywords are present in the found set
                if all(kw in found for kw in keywords):
                    self.log('All keywords found:', found)
                    winsound.Beep(1000, 300)
                    break
            if mode == 'any' and len(found) > 0:
                self.log('Found keywords:', found)
                winsound.Beep(1000, 300)
                break

            # click reroll while preserving the current mouse position
            rx, ry = reroll
            try:
                rx_i, ry_i = int(rx), int(ry)
                self.log('Clicking at', rx_i, ry_i)
                cur_x, cur_y = pyautogui.position()
                pyautogui.moveTo(rx_i, ry_i, duration=0)
                pyautogui.click()
                pyautogui.moveTo(cur_x, cur_y, duration=0)
            except Exception as e:
                self.log('Click error:', e)
            time.sleep(delay)

        self.log('Worker finished')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')


if __name__ == '__main__':
    root = tk.Tk()
    app = WorldPickerGUI(root)
    root.mainloop()
