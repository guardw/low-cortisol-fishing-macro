import tkinter as tk
from tkinter import ttk

import os
import json
import threading
import time
import keyboard

from PIL import ImageGrab, ImageOps, ImageEnhance, ImageFilter, Image
import pytesseract

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.defaults = {
            "bbox": [910, 490, 1010, 590],
            "hotkey_start": "F1",
            "hotkey_exit": "F2",
            "tolerance": "100",
            "delay": "0.15",
            "always_on_top": True
        }
        self.settings = self.load()

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                return self.defaults.copy()
        return self.defaults.copy()

    def save(self, settings=None):
        if settings:
            self.settings = settings
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()

class RegionSelector:
    def __init__(self, parent, initial_bbox):
        self.selected_bbox = None
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.square_size = 100

        left, top, right, bottom = initial_bbox
        self.square_x = left
        self.square_y = top

        self.overlay = tk.Toplevel(parent)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-alpha', 0.2)
        self.overlay.configure(bg='black')
        self.overlay.title("Drag square to position")

        self.canvas = tk.Canvas(self.overlay, bg='black', highlightthickness=0, cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.screen_width = self.overlay.winfo_screenwidth()
        self.screen_height = self.overlay.winfo_screenheight()

        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Escape>', lambda e: self.finish())
        self.overlay.bind('<Escape>', lambda e: self.finish())

        self.draw_square()

    def draw_square(self):
        self.canvas.delete('all')
        self.canvas.create_rectangle(0, 0, self.screen_width, self.screen_height,
                                     fill='black', stipple='gray50', outline='')

        left = self.square_x
        top = self.square_y
        right = self.square_x + self.square_size
        bottom = self.square_y + self.square_size

        self.canvas.create_rectangle(left, top, right, bottom,
                                     outline='#FF00FF', width=4, fill='')

        handle_size = 3
        for x, y in [(left, top), (right, top), (left, bottom), (right, bottom)]:
            self.canvas.create_rectangle(x-handle_size, y-handle_size, x+handle_size, y+handle_size,
                                        fill='#FF00FF', outline='white', width=2)

        cx, cy = left + self.square_size // 2, top + self.square_size // 2
        self.canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill='#FF00FF', outline='white', width=2)

        info = f"X:{left}  Y:{top}  SIZE:{self.square_size}x{self.square_size}"
        self.canvas.create_rectangle(10, 10, 350, 50, fill='#1a1a1a', outline='#FF00FF', width=2)
        self.canvas.create_text(15, 32, text=info, fill='#FF00FF', font=('Courier', 11, 'bold'), anchor='w')

        instructions = "Drag square to position  |  Right-click or ESC to finish"
        self.canvas.create_text(self.screen_width//2, self.screen_height-100, text=instructions,
                               fill="#FF0000", font=('Courier', 15), anchor='center')

    def on_mouse_down(self, event):
        left = self.square_x
        top = self.square_y
        right = self.square_x + self.square_size
        bottom = self.square_y + self.square_size
        
        if left <= event.x <= right and top <= event.y <= bottom:
            self.dragging = True
            self.drag_offset_x = event.x - left
            self.drag_offset_y = event.y - top

    def on_mouse_drag(self, event):
        if self.dragging:
            self.square_x = event.x - self.drag_offset_x
            self.square_y = event.y - self.drag_offset_y

            self.square_x = max(0, min(self.square_x, self.screen_width - self.square_size))
            self.square_y = max(0, min(self.square_y, self.screen_height - self.square_size))
            
            self.draw_square()

    def on_mouse_up(self, event):
        self.dragging = False

    def on_right_click(self, event):
        self.finish()

    def finish(self):
        left = self.square_x
        top = self.square_y
        right = self.square_x + self.square_size
        bottom = self.square_y + self.square_size
        
        self.selected_bbox = (left, top, right, bottom)
        self.overlay.destroy()

class BridgerMacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bridger Western Macro")
        self.root.geometry("400x350")
        self.root.resizable(False, False)

        self.settings_manager = SettingsManager()

        style = ttk.Style()
        style.theme_use('clam')

        self.is_running = False
        self.hotkey_start = self.settings_manager.get("hotkey_start", "F1")
        self.hotkey_exit = self.settings_manager.get("hotkey_exit", "F2")

        bbox = self.settings_manager.get("bbox", [910, 490, 1010, 590])
        self.bbox = tuple(bbox)

        self.tabControl = ttk.Notebook(root)
        self.tab_main = ttk.Frame(self.tabControl)
        self.tab_tesseract = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab_main, text='Main')
        self.tabControl.add(self.tab_tesseract, text='Tesseract')
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

        self.setup_main_tab()
        self.setup_tesseract_tab()
        self.setup_hotkeys()

        self.macro_thread = threading.Thread(target=self.macro_loop, daemon=True)
        self.macro_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_main_tab(self):
        self.drawing = False

        hotkey_frame = ttk.LabelFrame(self.tab_main, text="Hotkeys", padding=10)
        hotkey_frame.pack(fill="x", padx=10, pady=5)

        start_row = ttk.Frame(hotkey_frame)
        start_row.pack(fill="x", pady=5)
        tk.Label(start_row, text="Start/Stop:", font=("Arial", 10)).pack(side="left")
        self.lbl_f1 = tk.Label(start_row, text=self.hotkey_start, font=("Arial", 10, "bold"), fg="green")
        self.lbl_f1.pack(side="left", padx=10)

        exit_row = ttk.Frame(hotkey_frame)
        exit_row.pack(fill="x", pady=5)
        tk.Label(exit_row, text="Force Exit:", font=("Arial", 10)).pack(side="left")
        tk.Label(exit_row, text=self.hotkey_exit, font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=10)

        region_frame = ttk.LabelFrame(self.tab_main, text="OCR Region", padding=10)
        region_frame.pack(fill="x", padx=10, pady=5)

        self.coords_label = tk.Label(region_frame, text=self.format_bbox_display(), font=("Courier", 9), fg="#0099FF")
        self.coords_label.pack(anchor="w", pady=5)

        tk.Button(region_frame, text="Select Region on Screen", command=self.open_region_selector,
                 bg="#0099FF", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8).pack(fill="x", pady=5)

        options_frame = ttk.LabelFrame(self.tab_main, text="Options", padding=10)
        options_frame.pack(fill="x", padx=10, pady=5)

        self.always_on_top_var = tk.BooleanVar(value=self.settings_manager.get("always_on_top", True))
        tk.Checkbutton(options_frame, text="Always On Top", variable=self.always_on_top_var,
                      command=self.toggle_topmost, font=("Arial", 9)).pack(anchor="w")
        self.toggle_topmost()

        status_frame = ttk.Frame(hotkey_frame)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.status_label = tk.Label(status_frame, text="Status: Stopped", fg="red",
                                    font=("Arial", 9, "bold"), relief="sunken", padx=1, pady=1)
        self.status_label.pack(fill="both", expand=True)

        last_clicked = ttk.Frame(hotkey_frame)
        last_clicked.pack(fill="both", expand=True, padx=10, pady=5)

        self.last_clickedf = tk.Label(status_frame, text="last clicked:", fg="black",
                                    font=("Arial", 9, "bold"), relief="sunken", padx=2, pady=2)
        self.last_clickedf.pack(fill="both", expand=False)

    def setup_tesseract_tab(self):
        ocr_frame = ttk.LabelFrame(self.tab_tesseract, text="OCR Settings", padding=15)
        ocr_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tolerance_frame = ttk.Frame(ocr_frame)
        tolerance_frame.pack(fill="x", pady=8)
        tk.Label(tolerance_frame, text="Tolerance:", font=("Arial", 10), width=15).pack(side="left", padx=5)

        self.tolerance_entry = tk.Entry(tolerance_frame, width=12, font=("Arial", 10))
        self.tolerance_entry.insert(0, self.settings_manager.get("tolerance", "100"))
        self.tolerance_entry.pack(side="left", padx=5)

        delay_frame = ttk.Frame(ocr_frame)
        delay_frame.pack(fill="x", pady=8)
        tk.Label(delay_frame, text="Delay (sec):", font=("Arial", 10), width=15).pack(side="left", padx=5)

        self.delay_entry = tk.Entry(delay_frame, width=12, font=("Arial", 10))
        self.delay_entry.insert(0, self.settings_manager.get("delay", "0.15"))
        self.delay_entry.pack(side="left", padx=5)

        whitelist_frame = ttk.Frame(ocr_frame)
        whitelist_frame.pack(fill="x", pady=8)
        tk.Label(whitelist_frame, text="Whitelist:", font=("Arial", 10), width=15).pack(side="left", padx=5)
        tk.Label(whitelist_frame, text="T  G  F  R", font=("Courier", 10, "bold"), fg="#00AA00").pack(side="left", padx=5)

        ttk.Separator(ocr_frame, orient='horizontal').pack(fill="x", pady=15)
        tk.Button(ocr_frame, text="🧪 Test OCR", width=20, command=self.test_ocr,
                 bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), padx=10, pady=8).pack(fill="x", pady=5)

        self.test_result_lbl = tk.Label(ocr_frame, text="Ready to test", font=("Arial", 10),
                                       relief="sunken", padx=10, pady=8)
        self.test_result_lbl.pack(fill="x", pady=5)

    def toggle_topmost(self):
        self.root.attributes('-topmost', self.always_on_top_var.get())

    def format_bbox_display(self):
        left, top, right, bottom = self.bbox
        width = right - left
        height = bottom - top
        return f"X:{left} Y:{top} W:{width} H:{height}"

    def open_region_selector(self):
        if self.drawing: return
        self.drawing = True

        selector = RegionSelector(self.root, self.bbox)
        self.root.wait_window(selector.overlay)

        if selector.selected_bbox:
            self.bbox = selector.selected_bbox
            self.coords_label.config(text=self.format_bbox_display())
            self.settings_manager.set("bbox", list(self.bbox))
            self.drawing = False

    def setup_hotkeys(self):
        keyboard.add_hotkey(self.hotkey_start, self.toggle_macro)
        keyboard.add_hotkey(self.hotkey_exit, self.force_exit)

    def toggle_macro(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.status_label.config(text="Status: RUNNING", fg="green")
        else:
            self.status_label.config(text="Status: Stopped", fg="red")

    def force_exit(self):
        self.is_running = False
        self.root.quit()

    def process_image_for_ocr(self):
        img = ImageGrab.grab(self.bbox)
        new_size = (img.width * 2, img.height * 2)
        img = img.resize(new_size, Image.LANCZOS)

        img_gray = ImageOps.grayscale(img)

        enhancer = ImageEnhance.Contrast(img_gray)
        img_contrast = enhancer.enhance(3.0)

        enhancer = ImageEnhance.Sharpness(img_contrast)
        img_sharp = enhancer.enhance(2.0)

        try:
            tolerance = int(self.tolerance_entry.get())
        except ValueError:
            tolerance = 100

        img_inverted = ImageOps.invert(img_sharp)
        img_binary = img_inverted.point(lambda x: 255 if x > tolerance else 0)
        img_binary = img_binary.filter(ImageFilter.MedianFilter(size=3))

        custom_config = r'--psm 13 -c tessedit_char_whitelist=TGFRtgfr'

        try:
            text = pytesseract.image_to_string(img_binary, config=custom_config).strip().upper()
        except Exception as e:
            text = ""

        return text

    def test_ocr(self):
        try:
            detected_letter = self.process_image_for_ocr()
            if detected_letter in ['T', 'G', 'F', 'R']:
                self.test_result_lbl.config(text=f"Success! Detected: '{detected_letter}'", fg="green")
            else:
                self.test_result_lbl.config(text=f"Detected nothing valid (Raw: '{detected_letter}')", fg="red")
        except Exception as e:
            self.test_result_lbl.config(text="OCR Error. Is Tesseract installed?", fg="red")

    def macro_loop(self):
        while True:
            if self.is_running:
                try:
                    delay = float(self.delay_entry.get())
                    detected_letter = self.process_image_for_ocr()

                    if detected_letter in ['T', 'G', 'F', 'R']:
                        self.last_clickedf.config(text=str(detected_letter))
                        keyboard.send(detected_letter.lower())

                    time.sleep(delay)
                except Exception as e:
                    time.sleep(1)
            else:
                time.sleep(0.1)

    def on_closing(self):
        self.settings_manager.set("tolerance", self.tolerance_entry.get())
        self.settings_manager.set("delay", self.delay_entry.get())
        self.settings_manager.set("always_on_top", self.always_on_top_var.get())
        self.is_running = False
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = BridgerMacroApp(root)
    root.mainloop()