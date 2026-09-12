# LD2 to Apple macOS Dictionary Converter (`convert_ld2.py`)

A fast, standalone Python tool to convert **Lingoes (`.ld2`)** dictionary files into native **Apple macOS Dictionary (`.dictionary`)** bundles for use in macOS **Dictionary.app**, Spotlight, and system-wide **3-finger tap / "Look Up"**.

---

## Features

- **Direct LD2 Decompression**: Parses proprietary Lingoes LD2 binary structures and multi-stream zlib/deflate blocks without third-party dictionary software.
- **Cross-Reference & Inflection Resolution**: Seamlessly resolves word inflections, alternative definitions, and synonyms.
- **Native Apple Typography**: Styled with Apple's official `ui-serif` (New York / Georgia) serif typography and standard system font scaling.
- **Optimized for macOS "Look Up"**: Includes special overrides for the `html.apple_client-panel` quick look popover with crisp, bold, easily readable weights.
- **Full Dark Mode Support**: Uses dynamic macOS semantic colors (`CanvasText`) that automatically adapt to light and dark system appearances.
- **One-Command Install**: Generates Apple Dictionary XML, CSS, plist metadata, compiles with Apple DDK, and optionally installs directly into `~/Library/Dictionaries/`.

---

## Requirements

- **macOS** 10.11 or later (including macOS 14 Sonoma, macOS 15 Sequoia, and later).
- **Python 3.8+** (standard Python library only — no pip dependencies required!).
- **Rosetta 2** (if running on Apple Silicon / M-series Macs for Apple DDK helper binaries).
- **Xcode Command Line Tools** (for standard tools like `make`):
  ```bash
  xcode-select --install
  ```

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/medre22932-png/ld2-to-apple-dictionary.git
cd ld2-to-apple-dictionary
```

### 2. Convert a dictionary
Place your `.ld2` file in the folder, then run:

```bash
# Convert a specific dictionary and install it into macOS Dictionary:
python3 convert_ld2.py --install "MyDictionary.ld2"
```

```bash
# Or convert all .ld2 files in the current folder at once:
python3 convert_ld2.py --install
```

*(Note: On first run, the tool will automatically fetch the Apple Dictionary Development Kit tools if not present on your system).*

---

## Activating in macOS Dictionary

1. Open **Dictionary.app** on your Mac.
2. Open **Settings / Preferences** (`Cmd + ,`).
3. Scroll down the dictionary list, check the box next to your new dictionary, and drag it to your desired priority order.
4. You can now look up words in Dictionary.app or highlight any word in Safari, Mail, Preview, or Notes and use **Three-Finger Tap** or **Right-Click → Look Up**.

---

## Command-Line Options

```
usage: convert_ld2.py [-h] [--ddk DDK] [--install] [--output-dir OUTPUT_DIR] [input ...]

Convert Lingoes LD2 dictionaries to Apple Dictionary (.dictionary)

positional arguments:
  input                  Path to .ld2 file(s). If none specified, converts all .ld2 files in the current directory.

options:
  -h, --help             show this help message and exit
  --ddk DDK              Custom path to Apple Dictionary Development Kit folder (default: ./ddk)
  --install              Automatically install to ~/Library/Dictionaries and refresh macOS preferences
  --output-dir DIR       Custom temporary build directory
```

---

## Legal & Copyright Disclaimer

- **The Software**: This conversion script is an independent, clean-room implementation created for platform interoperability under the MIT License.
- **Dictionary Data**: This repository **does NOT contain any dictionary content**. Users are responsible for ensuring they have the legal right or license to use and convert any dictionary data they process with this tool.
- **Apple DDK**: Apple, macOS, and Dictionary are trademarks of Apple Inc.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
