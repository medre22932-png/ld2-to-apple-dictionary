#!/usr/bin/env python3
"""
Convert Lingoes (.ld2) dictionary files into Apple macOS (.dictionary) bundles.
"""

import sys
import os
import struct
import zlib
import re
import html
import subprocess
import argparse
import shutil
import plistlib
from pathlib import Path

DEFAULT_DDK_DIR = Path(__file__).resolve().parent / "ddk"

CSS_TEMPLATE = """@charset "UTF-8";
@namespace d url("http://www.apple.com/DTDs/DictionaryService-1.0.rng");

/* Native Apple Dictionary Typography with full weight */
html, body, d|entry {
    font-family: ui-serif, Georgia, "New York", "Times New Roman", serif !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    line-height: 1.55 !important;
    color: CanvasText !important;
    -webkit-font-smoothing: antialiased;
}

d|entry {
    padding: 8px 14px;
}

h1, *|h1 {
    font-family: ui-serif, Georgia, "New York", "Times New Roman", serif !important;
    font-size: 19px !important;
    font-weight: 700 !important;
    line-height: 1.3 !important;
    margin: 0 0 6px 0 !important;
    color: CanvasText !important;
    letter-spacing: normal !important;
}

.phonetic, *|.phonetic {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 450 !important;
    color: #6e6e73 !important;
    margin-left: 6px !important;
}

.pos, *|.pos {
    display: inline-block !important;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    font-style: italic !important;
    color: #0071e3 !important;
    margin-right: 5px !important;
}

.meaning, *|.meaning {
    color: #1d8348 !important;
    font-weight: 500 !important;
}

.ref, *|.ref {
    font-family: ui-serif, Georgia, "New York", serif !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #0071e3 !important;
    margin: 3px 0 !important;
}

.ref a, *|.ref a {
    color: #0071e3 !important;
    text-decoration: none !important;
}

.ref a:hover {
    text-decoration: underline !important;
}

.def, *|.def, div.def {
    font-family: ui-serif, Georgia, "New York", "Times New Roman", serif !important;
    font-size: 14.5px !important;
    font-weight: 450 !important;
    line-height: 1.55 !important;
    color: CanvasText !important;
    margin-top: 4px !important;
}

.def b, *|.def b {
    font-weight: 700 !important;
}

.def i, *|.def i {
    font-style: italic !important;
}

/* ===================================================
   macOS "Look Up" Panel (Quick Look / 3-Finger Tap)
   =================================================== */
html.apple_client-panel,
html.apple_client-panel body,
html.apple_client-panel d|entry {
    font-family: ui-serif, Georgia, "New York", "Times New Roman", serif !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    color: CanvasText !important;
    padding: 1px 2px !important;
}

html.apple_client-panel h1,
html.apple_client-panel *|h1 {
    font-family: ui-serif, Georgia, "New York", "Times New Roman", serif !important;
    font-size: 17.5px !important;
    font-weight: 700 !important;
    margin-bottom: 4px !important;
    color: CanvasText !important;
}

html.apple_client-panel .phonetic,
html.apple_client-panel *|.phonetic {
    font-size: 12px !important;
    font-weight: 450 !important;
}

html.apple_client-panel .pos,
html.apple_client-panel *|.pos {
    font-size: 12px !important;
    font-weight: 600 !important;
}

html.apple_client-panel .def,
html.apple_client-panel *|.def,
html.apple_client-panel div {
    font-family: ui-serif, Georgia, "New York", "Times New Roman", serif !important;
    font-size: 14.5px !important;
    font-weight: 450 !important;
    line-height: 1.5 !important;
    color: CanvasText !important;
}

html.apple_client-panel .ref,
html.apple_client-panel *|.ref {
    font-size: 13.5px !important;
    font-weight: 500 !important;
}

/* ===================================================
   Dark Mode Support
   =================================================== */
@media (prefers-color-scheme: dark) {
    .pos, *|.pos {
        color: #2997ff !important;
    }
    .meaning, *|.meaning {
        color: #30d158 !important;
    }
    .ref a, *|.ref a {
        color: #2997ff !important;
    }
    .phonetic, *|.phonetic {
        color: #98989d !important;
    }
}
"""

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>English</string>
	<key>CFBundleIdentifier</key>
	<string>{bundle_id}</string>
	<key>CFBundleDisplayName</key>
	<string>{display_name}</string>
	<key>CFBundleName</key>
	<string>{bundle_name}</string>
	<key>CFBundleShortVersionString</key>
	<string>1.0</string>
	<key>DCSDictionaryCopyright</key>
	<string>Converted from Lingoes LD2</string>
	<key>DCSDictionaryManufacturerName</key>
	<string>Custom Dictionary</string>
</dict>
</plist>
"""

def clean_xml_content(raw_xml: str) -> tuple[str, str]:
    """
    Parse Lingoes XML formatting and convert to valid, clean XHTML.
    Returns (phonetic_text, cleaned_body_xhtml).
    """
    # Remove null and invalid control characters
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', raw_xml)
    
    # Extract phonetic / pronunciation if present in <H><L>...</L></H>
    phonetic = ""
    m_h = re.search(r'<H\b[^>]*>(.*?)</H>', text, re.DOTALL)
    if m_h:
        h_content = m_h.group(1)
        m_l = re.search(r'<L\b[^>]*>(.*?)</L>', h_content, re.DOTALL)
        if m_l:
            phonetic = m_l.group(1).strip()
        text = text[:m_h.start()] + text[m_h.end():]
    
    # Clean any remaining empty or self-closing H tags
    text = re.sub(r'<H\s*\/?>', '', text)
    text = re.sub(r'</H>', '', text)
    
    # Handle CDATA if wrapped
    cdata_m = re.search(r'<!\[CDATA\[(.*?)\]\]>', text, re.DOTALL)
    if cdata_m:
        text = cdata_m.group(1)
    
    # Replace semantic tags
    text = re.sub(r'<U\b[^>]*>(.*?)</U>', r'<span class="pos">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'<M\b[^>]*>(.*?)</M>', r'<span class="meaning">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'<g\b[^>]*>(.*?)</g>', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'<h\b[^>]*>(.*?)</h>', r'<i>\1</i>', text, flags=re.DOTALL)
    
    # Links / cross-references
    text = re.sub(r'<Y\s+O="([^"]*)">(.*?)</Y>', r'<a href="x-dictionary:d:\1">\2</a>', text, flags=re.DOTALL)
    
    # Line breaks
    text = re.sub(r'<n\s*\/?>', '<br/>', text)
    text = re.sub(r'<br\s*>', '<br/>', text)
    
    # Strip remaining Lingoes structural tags: C, F, I, N, Q, Ô, etc.
    text = re.sub(r'</?(?:C|F|I|N|Q|Ô|L)\b[^>]*>', ' ', text)
    
    # Ensure any stray unescaped & is &amp;
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    
    # Clean multiple spaces and trim
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'(\s*<br\/>\s*)+', '<br/>', text)
    text = text.strip()
    
    phonetic = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', phonetic).strip()
    return phonetic, text


class LD2Extractor:
    def __init__(self, ld2_path: str):
        self.ld2_path = os.path.abspath(ld2_path)
        with open(self.ld2_path, "rb") as f:
            self.data = f.read()
        self._parse_header()

    def _parse_header(self):
        data = self.data
        if data[:4] != b"?LD2":
            raise ValueError(f"Not a valid LD2 file (invalid magic: {data[:4]})")
        
        offset_data = struct.unpack_from("<I", data, 0x5C)[0] + 0x60
        dtype = struct.unpack_from("<I", data, offset_data)[0]
        offset_with_info = struct.unpack_from("<I", data, offset_data + 4)[0] + offset_data + 12
        
        od = offset_data if dtype == 3 else offset_with_info
        limit = struct.unpack_from("<I", data, od + 4)[0] + od + 8
        offset_index = od + 0x1C
        offset_compressed_header = struct.unpack_from("<I", data, od + 8)[0] + offset_index
        
        self.inflated_words_index_len = struct.unpack_from("<I", data, od + 12)[0]
        self.inflated_words_len = struct.unpack_from("<I", data, od + 16)[0]
        
        pos = offset_compressed_header + 8
        off = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        
        deflate_streams = []
        while (off + pos) < limit:
            off = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            deflate_streams.append(off)
            
        self.deflate_streams = deflate_streams
        self.stream_start_offset = pos

    def decompress(self) -> bytes:
        data = self.data
        start_offset = self.stream_start_offset
        last_offset = start_offset
        chunks = []
        for off_rel in self.deflate_streams:
            cur_offset = start_offset + off_rel
            chunks.append(zlib.decompress(data[last_offset:cur_offset]))
            last_offset = cur_offset
        return b"".join(chunks)


def enable_in_preferences(dict_path: Path):
    """Enable dictionary in Dictionary.app preferences plist if available."""
    try:
        plist_path = Path.home() / "Library" / "Containers" / "com.apple.Dictionary" / "Data" / "Library" / "Preferences" / "com.apple.Dictionary.plist"
        if not plist_path.exists():
            return
        with open(plist_path, "rb") as f:
            prefs = plistlib.load(f)
        
        str_path = str(dict_path.resolve())
        lad = prefs.setdefault("last available dictionaries", [])
        if str_path not in lad:
            lad.insert(0, str_path)
            
        ws = prefs.get("window settings", [])
        if ws:
            dicts = ws[0].setdefault("dictionaries", [])
            paths = [d.get("path") for d in dicts]
            if str_path not in paths:
                dicts.insert(0, {
                    "disclosure opened": True,
                    "path": str_path,
                    "user choice": True
                })
        with open(plist_path, "wb") as f:
            plistlib.dump(prefs, f)
        subprocess.run(["killall", "cfprefsd"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "LookupViewService"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "DictionaryServiceHelper"], capture_output=True)
    except Exception as e:
        print(f"    [!] Note: Could not auto-update preferences: {e}")


def ensure_ddk(ddk_path: Path):
    """Ensure the Apple Dictionary Development Kit tools exist, downloading if needed."""
    build_script = ddk_path / "bin" / "build_dict.sh"
    if build_script.exists():
        return
    # Check system path
    sys_ddk = Path("/Applications/Utilities/Dictionary Development Kit")
    if (sys_ddk / "bin" / "build_dict.sh").exists():
        return
    print(f"[*] Apple Dictionary Development Kit not found at {ddk_path}.")
    print("[*] Downloading Apple DDK tools for macOS...")
    ddk_path.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "git", "clone", "--depth", "1",
        "https://github.com/drewtu2/Apple-Dictionary-Development-Kit.git",
        str(ddk_path)
    ], check=True)
    for b in (ddk_path / "bin").glob("*"):
        b.chmod(0o755)
    print("[✓] Apple DDK ready!\n")


def convert_ld2_to_apple_dict(ld2_path: str, output_dir: str = None, ddk_dir: str = None, install: bool = False):
    ld2_file = Path(ld2_path).resolve()
    dict_base_name = ld2_file.stem
    
    print(f"==================================================")
    print(f"Processing: {dict_base_name}")
    print(f"==================================================")
    
    if output_dir is None:
        work_dir = ld2_file.parent / f"build_{dict_base_name.replace(' ', '_')}"
    else:
        work_dir = Path(output_dir) / f"build_{dict_base_name.replace(' ', '_')}"
    
    work_dir.mkdir(parents=True, exist_ok=True)
    
    if ddk_dir is None:
        ddk_path = DEFAULT_DDK_DIR
    else:
        ddk_path = Path(ddk_dir).resolve()
        
    ensure_ddk(ddk_path)
    
    # Check if system path has it if local doesn't
    build_dict_script = ddk_path / "bin" / "build_dict.sh"
    if not build_dict_script.exists():
        sys_ddk = Path("/Applications/Utilities/Dictionary Development Kit")
        if (sys_ddk / "bin" / "build_dict.sh").exists():
            ddk_path = sys_ddk
            build_dict_script = ddk_path / "bin" / "build_dict.sh"
            
    if not build_dict_script.exists():
        raise FileNotFoundError(f"build_dict.sh not found at {build_dict_script}")

    # 1. Decompress LD2
    print(f"[*] Decompressing {ld2_file.name}...")
    extractor = LD2Extractor(str(ld2_file))
    inflated = extractor.decompress()
    print(f"    Inflated data size: {len(inflated):,} bytes")

    off_defs = extractor.inflated_words_index_len
    off_xml = extractor.inflated_words_index_len + extractor.inflated_words_len
    data_len = 10
    total_entries = (off_defs // data_len) - 1
    print(f"    Total entries to process: {total_entries:,}")

    def get_entry(idx: int):
        p = data_len * idx
        w0, x0 = struct.unpack_from("<II", inflated, p)
        refs = inflated[p + 9]
        w1, x1 = struct.unpack_from("<II", inflated, p + 10)
        ref_indices = []
        lw = w0
        for _ in range(refs):
            if off_defs + lw + 4 <= len(inflated):
                rid = struct.unpack_from("<I", inflated, off_defs + lw)[0]
                if rid < total_entries and rid != idx:
                    ref_indices.append(rid)
            lw += 4
        raw_word = inflated[off_defs + lw : off_defs + w1].decode("utf-8", errors="ignore").strip()
        word = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', raw_word)
        return word, x0, x1, ref_indices

    # Safe file names without spaces for build tools
    safe_name = dict_base_name.replace(" ", "_").replace("-", "_")
    xml_path = work_dir / f"{safe_name}.xml"
    css_path = work_dir / f"{safe_name}.css"
    plist_path = work_dir / f"{safe_name}.plist"

    # Write CSS
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(CSS_TEMPLATE)

    # Write Info.plist
    bundle_id = f"com.apple.dictionary.{safe_name}"
    display_name = dict_base_name
    with open(plist_path, "w", encoding="utf-8") as f:
        f.write(PLIST_TEMPLATE.format(
            bundle_id=bundle_id,
            display_name=html.escape(display_name),
            bundle_name=safe_name
        ))

    # 2. Write Apple Dictionary XML
    print(f"[*] Generating Apple Dictionary XML: {xml_path.name}...")
    written_count = 0
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')
        
        for i in range(total_entries):
            try:
                word, x0, x1, ref_indices = get_entry(i)
                if not word:
                    continue
                
                xml_parts = []
                if x1 > x0:
                    raw = inflated[off_xml + x0 : off_xml + x1].decode("utf-8", errors="ignore")
                    if raw.strip():
                        xml_parts.append(raw)
                
                ref_titles = []
                for rid in ref_indices:
                    ref_w, rx0, rx1, _ = get_entry(rid)
                    if ref_w:
                        ref_titles.append(ref_w)
                    if rx1 > rx0:
                        raw_rx = inflated[off_xml + rx0 : off_xml + rx1].decode("utf-8", errors="ignore")
                        if raw_rx.strip():
                            xml_parts.append(raw_rx)
                
                # Format XML content
                raw_body = " <br/> ".join(xml_parts)
                phonetic, cleaned_body = clean_xml_content(raw_body)
                
                # If body is empty but has reference title
                if not cleaned_body and ref_titles:
                    links = ", ".join(f'<a href="x-dictionary:d:{html.escape(r, quote=True)}">{html.escape(r)}</a>' for r in ref_titles)
                    cleaned_body = f'<span class="ref">→ {links}</span>'
                
                entry_id = f"entry_{i}"
                safe_title = html.escape(word, quote=True)
                
                f.write(f'<d:entry id="{entry_id}" d:title="{safe_title}">\n')
                f.write(f'  <d:index d:value="{safe_title}"/>\n')
                f.write(f'  <h1>{safe_title}')
                if phonetic:
                    f.write(f'<span class="phonetic">[{html.escape(phonetic)}]</span>')
                f.write('</h1>\n')
                
                f.write(f'  <div class="def">{cleaned_body}</div>\n')
                f.write('</d:entry>\n')
                written_count += 1
                
                if (i + 1) % 100000 == 0:
                    print(f"    Extracted {i + 1:,}/{total_entries:,} entries...")
            except Exception as e:
                continue

        f.write('</d:dictionary>\n')

    print(f"    Successfully wrote {written_count:,} entries to XML.")

    # 3. Compile with build_dict.sh
    print(f"[*] Compiling into macOS .dictionary bundle with Apple DDK...")
    env = os.environ.copy()
    env["DICT_BUILD_TOOL_DIR"] = str(ddk_path)
    env["DICT_DEV_KIT_OBJ_DIR"] = str(work_dir / "objects")

    cmd = [
        str(build_dict_script),
        "-v", "10.11",
        dict_base_name,
        f"{safe_name}.xml",
        f"{safe_name}.css",
        f"{safe_name}.plist"
    ]

    result = subprocess.run(cmd, cwd=str(work_dir), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Build failed! STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        raise RuntimeError(f"build_dict.sh failed with exit code {result.returncode}")

    built_dict = work_dir / "objects" / f"{dict_base_name}.dictionary"
    if not built_dict.exists():
        built_dict = work_dir / "objects" / f"{safe_name}.dictionary"
    
    if not built_dict.exists():
        raise FileNotFoundError(f"Expected compiled dictionary at {built_dict}")

    final_dest = ld2_file.parent / f"{dict_base_name}.dictionary"
    if final_dest.exists():
        shutil.rmtree(final_dest)
    shutil.copytree(built_dict, final_dest)
    print(f"[✓] Created dictionary at: {final_dest}")

    # 4. Optional Install
    if install:
        user_dict_dir = Path.home() / "Library" / "Dictionaries"
        user_dict_dir.mkdir(parents=True, exist_ok=True)
        install_target = user_dict_dir / f"{dict_base_name}.dictionary"
        if install_target.exists():
            shutil.rmtree(install_target)
        shutil.copytree(final_dest, install_target)
        subprocess.run(["touch", str(user_dict_dir)])
        enable_in_preferences(install_target)
        print(f"[✓] Installed to: {install_target}")

    # Clean up workdir objects
    shutil.rmtree(work_dir, ignore_errors=True)
    print(f"[✓] Done with {dict_base_name}!\n")
    return final_dest


def main():
    parser = argparse.ArgumentParser(description="Convert Lingoes LD2 dictionaries to Apple Dictionary (.dictionary)")
    parser.add_argument("input", nargs="*", help="Path to .ld2 file(s). If none specified, converts all .ld2 in current folder.")
    parser.add_argument("--ddk", default=str(DEFAULT_DDK_DIR), help="Path to Apple Dictionary Development Kit folder")
    parser.add_argument("--install", action="store_true", help="Automatically install to ~/Library/Dictionaries")
    parser.add_argument("--output-dir", default=None, help="Temporary build directory")

    args = parser.parse_args()

    files = args.input
    if not files:
        files = sorted([f for f in os.listdir(".") if f.endswith(".ld2")])

    if not files:
        print("No .ld2 files found to convert!")
        sys.exit(1)

    print(f"Found {len(files)} dictionary file(s) to convert:")
    for f in files:
        print(f" - {f}")
    print()

    for f in files:
        try:
            convert_ld2_to_apple_dict(f, output_dir=args.output_dir, ddk_dir=args.ddk, install=args.install)
        except Exception as e:
            print(f"[!] Error converting {f}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
