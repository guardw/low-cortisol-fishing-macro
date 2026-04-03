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

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki

## Running

Execute the macro:
```bash
python main.py
```

## Building Standalone Executable

Build a portable EXE file that doesn't require Python:

### Windows
Double-click `build.bat` or run:
```bash
pyinstaller --onefile --windowed --name BridgerWestern main.py
```

The executable will be in the `dist/` folder.

## Settings

All settings are automatically saved to `settings.json`:
- OCR region coordinates
- Tolerance and delay values
- Always-on-top preference
- Hotkey assignments

Settings persist between sessions.