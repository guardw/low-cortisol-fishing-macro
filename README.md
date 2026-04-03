# low cortisol fishing macro

ai generated read me cuz IDGAF

## Features

- OCR detection with customizable tolerance and delay
- Draggable region selector for OCR area
- Hotkey support (F1 to toggle, F2 to exit)
- Settings persistence (automatically saves all preferences)
- Always-on-top window option

## Requirements

- Python 3.8+
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`

## Installation when running main.py

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. MUST Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki
  
   ^ above still requires you to do this with exe file

## Settings

All settings are automatically saved to `settings.json`:
- OCR region coordinates
- Tolerance and delay values
- Always-on-top preference
- Hotkey assignments

Settings persist between sessions.
