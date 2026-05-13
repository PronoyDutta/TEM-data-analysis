# Panta Rhei Image Converter (TEM Analysis Tool)

A professional tool for batch-converting and live-monitoring Panta Rhei TEM (`.prz`) files into high-quality PNG images for publication.

## Features

- **Batch Mode**: Select multiple `.prz` files and convert them all at once.
- **Live Folder Watcher**: Automatically converts new files as they are saved by your microscope software.
- **Auto-Scalebar**: Automatically calculates "nice" scalebar values based on image magnification.
- **Auto-Contrast**: Applies optimal contrast stretching (0.1% - 99.9% percentile).
- **Persistent Settings**: Remembers your favorite folders and settings.
- **Standalone Executable**: Works without needing Python installed.

## Installation

### For Users
Download the latest `panta_rhei_exporter.exe` from the `dist` folder and run it directly.

### For Developers
1. Clone this repository.
2. Create a virtual environment and install dependencies:
   ```bash
   pip install numpy matplotlib Pillow
   ```
3. Run the script:
   ```bash
   python panta_rhei_exporter.py
   ```

## License
MIT
