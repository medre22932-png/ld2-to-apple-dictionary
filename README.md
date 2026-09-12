# LD2 to Apple macOS Dictionary Converter (`convert_ld2.py`)

A fast, standalone Python tool to convert **Lingoes (`.ld2`)** dictionary files into native **Apple macOS Dictionary (`.dictionary`)** bundles for use in macOS **Dictionary.app**, Spotlight, and system-wide **3-finger tap / "Look Up"**.

---

## Requirements

> [!WARNING]
> **macOS Only**: This tool can only be used on macOS. The output `.dictionary` bundle is Apple's native dictionary format, and compiling it requires Apple's Dictionary Development Kit compiler tools, which only run on macOS (Darwin). Windows and Linux are not supported for dictionary output.

- **macOS** 10.11 or later.
- **Python 3.8+** (standard Python library only — no `pip install` required!).
- **Xcode Command Line Tools**: Provides standard Apple development tools. Most Mac users already have this. If not installed on your system, simply run this one-line command in Terminal:
  ```bash
  xcode-select --install
  ```
- **Rosetta 2** *(Apple Silicon / M-series Macs only)*: Apple's dictionary compiler binaries were originally built for Intel Macs, so M-series Macs run them via Apple's built-in Rosetta translation engine. Most users already have Rosetta installed; if your Mac asks for it, you can enable it with:
  ```bash
  softwareupdate --install-rosetta --agree-to-license
  ```

---

## Quick Start

### 1. Get the Script
You can clone the repository or simply download the Python script:

**Option A: Clone the repository**
```bash
git clone https://github.com/medre22932-png/ld2-to-apple-dictionary.git
cd ld2-to-apple-dictionary
```

**Option B: Download the script directly**
Download [`convert_ld2.py`](https://raw.githubusercontent.com/medre22932-png/ld2-to-apple-dictionary/main/convert_ld2.py) and place it in any folder on your Mac.

---

### 2. Apple Dictionary Development Kit (DDK)
**You don't need to download or set up anything manually!**  
The first time you run the script, it will detect that the compiler tools are missing and ask:
```text
[*] Apple Dictionary Development Kit was not found at '...'.
    Would you like to automatically download the DDK tools into ./ddk? [Y/n]: 
```
**Just press Enter or type `y` ("yes")**, and the script will automatically set up the tools for you.

---

### 3. Convert Your Dictionaries

#### Easiest: macOS File Dialog
Simply run the script without any arguments:
```bash
python3 convert_ld2.py
```
A native macOS file picker dialog will appear. Select one or more `.ld2` files, and the script will create the `.dictionary` package directly in the same folder where your `.ld2` file is located!

#### Command-Line Usage
You can also pass `.ld2` file paths directly:
```bash
# Convert a specific file (outputs .dictionary in the same folder):
python3 convert_ld2.py "/path/to/MyDictionary.ld2"

# Or convert AND immediately install into macOS Dictionary.app:
python3 convert_ld2.py --install "/path/to/MyDictionary.ld2"
```

---

## Activating in macOS Dictionary

1. If you didn't use `--install`, copy the resulting `.dictionary` file (or drag it into `~/Library/Dictionaries/`).
2. Open **Dictionary.app** on your Mac.
3. Open **Settings / Preferences** (`Cmd + ,`).
4. Scroll down the dictionary list, check the box next to your new dictionary, and drag it to your desired priority order.
5. You can now look up words in Dictionary.app or highlight any word in Safari, Mail, Preview, or Notes and use **Three-Finger Tap** or **Right-Click → Look Up**.

---

## Command-Line Options

```
usage: convert_ld2.py [-h] [--ddk DDK] [--download-ddk] [--install]
                      [--output-dir OUTPUT_DIR] [input ...]

Convert Lingoes LD2 dictionaries to Apple Dictionary (.dictionary)

positional arguments:
  input                 Path to .ld2 file(s). If none specified, opens a macOS
                        file selection dialog.

options:
  -h, --help            show this help message and exit
  --ddk DDK             Path to Apple Dictionary Development Kit folder
  --download-ddk        Automatically download Apple DDK tools if missing
  --install             Optionally install to ~/Library/Dictionaries (disabled
                        by default)
  --output-dir DIR      Temporary build directory
```

---

## Features

- **Direct LD2 Decompression**: Parses proprietary Lingoes LD2 binary structures and multi-stream zlib/deflate blocks without third-party dictionary software.
- **Cross-Reference & Inflection Resolution**: Seamlessly resolves word inflections, alternative definitions, and synonyms.
- **Native Apple Typography**: Styled with Apple's official `ui-serif` (New York / Georgia) serif typography and standard system font scaling.
- **Optimized for macOS "Look Up"**: Includes special overrides for the `html.apple_client-panel` quick look popover with crisp, bold, easily readable weights.
- **Full Dark Mode Support**: Uses dynamic macOS semantic colors (`CanvasText`) that automatically adapt to light and dark system appearances.
- **One-Command Install**: Generates Apple Dictionary XML, CSS, plist metadata, compiles with Apple DDK, and optionally installs directly into `~/Library/Dictionaries/`.

---

## Legal & Copyright Disclaimer

- **The Software**: This conversion script is an independent, clean-room implementation created for platform interoperability under the MIT License.
- **Dictionary Data**: This repository **does NOT contain any dictionary content**. Users are responsible for ensuring they have the legal right or license to use and convert any dictionary data they process with this tool.
- **Apple DDK**: Apple, macOS, and Dictionary are trademarks of Apple Inc.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
