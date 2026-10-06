#!/usr/bin/env python3
"""
Sticker Processor for Portrait-Sticker-Maker Skill.
Handles chroma-key magenta removal, grid sheet slicing, die-cut white border creation,
multi-platform export (LINE, Telegram, Discord, WeChat), and showcase montage generation.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageFont


def remove_chroma_key(
    img: Image.Image,
    key_color: Tuple[int, int, int] = (255, 0, 255),
    tolerance: int = 80,
    softness: int = 25,
) -> Image.Image:
    """
    Remove solid chroma-key background (default magenta #FF00FF).
    Uses numpy if available for maximum speed, falls back gracefully to pure Pillow.
    """
    img = img.convert("RGBA")
    try:
        import numpy as np

        arr = np.array(img, dtype=np.float32)
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        kr, kg, kb = key_color

        # Euclidean distance from chroma key color
        dist = np.sqrt((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2)

        # Alpha falloff curve
        alpha = np.clip((dist - tolerance) / max(1.0, float(softness)), 0.0, 1.0) * 255.0
        arr[..., 3] = np.minimum(arr[..., 3], alpha)

        # Magenta spill suppression on edges
        is_spill = (arr[..., 3] > 0) & (arr[..., 3] < 240)
        if np.any(is_spill):
            arr[is_spill, 0] = np.minimum(arr[is_spill, 0], (arr[is_spill, 1] + arr[is_spill, 2]) / 2 + 30)

        return Image.fromarray(arr.astype(np.uint8), "RGBA")

    except ImportError:
        # Pure Pillow implementation: No numpy required
        r, g, b, a = img.split()
        diff_r = ImageOps.invert(r) if key_color[0] == 255 else r
        diff_g = g if key_color[1] == 0 else ImageOps.invert(g)
        diff_b = ImageOps.invert(b) if key_color[2] == 255 else b

        sum1 = ImageChops.add(diff_r, diff_g)
        total_diff = ImageChops.add(sum1, diff_b)

        lut = []
        for i in range(256):
            if i <= tolerance:
                lut.append(0)
            elif i >= tolerance + softness:
                lut.append(255)
            else:
                lut.append(int(255 * (i - tolerance) / max(1, softness)))

        alpha_mask = total_diff.point(lut)
        final_alpha = ImageChops.darker(a, alpha_mask)
        img.putalpha(final_alpha)
        return img


def add_die_cut_border(
    img: Image.Image,
    border_width: int = 12,
    border_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    shadow_offset: Tuple[int, int] = (0, 6),
    shadow_blur: int = 8,
    shadow_opacity: int = 70,
) -> Image.Image:
    """
    Creates a physical vinyl / chat sticker die-cut white outline and subtle drop shadow.
    """
    img = img.convert("RGBA")
    w, h = img.size
    pad = border_width + max(abs(shadow_offset[0]), abs(shadow_offset[1])) + shadow_blur * 2

    # Canvas with padding to prevent clipping of borders & shadow
    canvas_w = w + pad * 2
    canvas_h = h + pad * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # Paste original subject in the center
    orig_pos = (pad, pad)
    temp_orig = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    temp_orig.paste(img, orig_pos, img)

    alpha = temp_orig.getchannel("A")

    # 1. Expand alpha mask to create white die-cut sticker outline
    filter_size = max(3, border_width * 2 + 1)
    # Ensure filter_size is odd
    if filter_size % 2 == 0:
        filter_size += 1
    expanded_alpha = alpha.filter(ImageFilter.MaxFilter(filter_size))

    # 2. Drop shadow
    if shadow_opacity > 0:
        shadow_mask = expanded_alpha.filter(ImageFilter.GaussianBlur(shadow_blur))
        # Scale shadow opacity
        shadow_lut = [int(v * (shadow_opacity / 255.0)) for v in range(256)]
        shadow_mask = shadow_mask.point(shadow_lut)
        shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        shadow_layer.putalpha(shadow_mask)

        # Shift shadow by offset
        shifted_shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        shifted_shadow.paste(shadow_layer, shadow_offset, shadow_layer)
        canvas = Image.alpha_composite(canvas, shifted_shadow)

    # 3. White border layer
    border_layer = Image.new("RGBA", (canvas_w, canvas_h), border_color)
    border_layer.putalpha(expanded_alpha)
    canvas = Image.alpha_composite(canvas, border_layer)

    # 4. Original subject on top
    canvas = Image.alpha_composite(canvas, temp_orig)

    # Auto crop excess transparent space while maintaining a clean 6px margin
    bbox = canvas.getbbox()
    if bbox:
        margin = 6
        crop_box = (
            max(0, bbox[0] - margin),
            max(0, bbox[1] - margin),
            min(canvas_w, bbox[2] + margin),
            min(canvas_h, bbox[3] + margin),
        )
        canvas = canvas.crop(crop_box)

    return canvas


def fit_to_box(
    img: Image.Image,
    target_width: int,
    target_height: int,
    padding: int = 10,
    expand_canvas: bool = True,
) -> Image.Image:
    """
    Scale image maintaining aspect ratio within (target_width - 2*padding, target_height - 2*padding).
    If expand_canvas is True, output is exact target_width x target_height with centered image.
    """
    max_w = target_width - padding * 2
    max_h = target_height - padding * 2

    w, h = img.size
    ratio = min(max_w / max(1, w), max_h / max(1, h))
    new_w = max(1, int(round(w * ratio)))
    new_h = max(1, int(round(h * ratio)))

    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if not expand_canvas:
        return resized

    canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
    paste_x = (target_width - new_w) // 2
    paste_y = (target_height - new_h) // 2
    canvas.paste(resized, (paste_x, paste_y), resized)
    return canvas


def slice_grid_sheet(
    sheet_path: Path,
    rows: int,
    cols: int,
    output_dir: Path,
    labels: Optional[List[str]] = None,
    chroma_key: bool = True,
    add_border: bool = True,
    border_width: int = 10,
) -> List[Path]:
    """
    Slice a multi-panel sprite sheet (e.g. 3x3 or 2x4) into individual sticker images.
    """
    img = Image.open(sheet_path)
    if chroma_key:
        img = remove_chroma_key(img)

    sheet_w, sheet_h = img.size
    cell_w = sheet_w // cols
    cell_h = sheet_h // rows

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []

    count = 0
    total_cells = rows * cols

    for r in range(rows):
        for c in range(cols):
            box = (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)
            cell = img.crop(box)

            # Check if cell has subject
            bbox = cell.getbbox()
            if not bbox:
                # Completely transparent/empty cell
                continue

            # Auto-crop to content inside the cell with a comfortable margin
            cell_cropped = cell.crop(bbox)

            if add_border:
                processed_cell = add_die_cut_border(
                    cell_cropped,
                    border_width=border_width,
                    border_color=(255, 255, 255, 255),
                    shadow_offset=(0, 4),
                    shadow_blur=6,
                )
            else:
                processed_cell = cell_cropped

            label = labels[count] if labels and count < len(labels) else f"sticker_{count+1:02d}"
            # Sanitize filename
            clean_label = "".join(c for c in label if c.isalnum() or c in ("-", "_")).strip()
            if not clean_label:
                clean_label = f"sticker_{count+1:02d}"

            out_path = output_dir / f"{count+1:02d}_{clean_label}.png"
            processed_cell.save(out_path, format="PNG")
            generated_files.append(out_path)

            count += 1
            if count >= total_cells:
                break

    return generated_files


def export_platform_packages(
    sticker_paths: List[Path],
    output_dir: Path,
    labels: Optional[List[str]] = None,
) -> dict[str, List[Path]]:
    """
    Export stickers into standardized folder structures for:
    - LINE (370x320 max, 10px safe margin)
    - Telegram / Discord (512x512 square)
    - WeChat (240x240 square)
    - Master HD (1024x1024 square)
    """
    dirs = {
        "line": output_dir / "line_370x320",
        "telegram_discord": output_dir / "telegram_discord_512x512",
        "wechat": output_dir / "wechat_240x240",
        "master_hd": output_dir / "master_hd_1024x1024",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    results: dict[str, List[Path]] = {k: [] for k in dirs}

    for idx, path in enumerate(sticker_paths):
        img = Image.open(path).convert("RGBA")
        name = path.stem

        # LINE: max 370 x 320, aspect ratio preserved, 10px safe margin
        line_img = fit_to_box(img, 370, 320, padding=10, expand_canvas=False)
        line_path = dirs["line"] / f"{idx+1:02d}.png"
        line_img.save(line_path, format="PNG")
        results["line"].append(line_path)

        # Telegram / Discord: 512 x 512 square canvas
        tg_img = fit_to_box(img, 512, 512, padding=16, expand_canvas=True)
        tg_path = dirs["telegram_discord"] / f"{name}.png"
        tg_img.save(tg_path, format="PNG")
        results["telegram_discord"].append(tg_path)

        # WeChat: 240 x 240 square canvas
        wc_img = fit_to_box(img, 240, 240, padding=10, expand_canvas=True)
        wc_path = dirs["wechat"] / f"{name}.png"
        wc_img.save(wc_path, format="PNG")
        results["wechat"].append(wc_path)

        # Master HD: 1024 x 1024 square canvas
        master_img = fit_to_box(img, 1024, 1024, padding=32, expand_canvas=True)
        master_path = dirs["master_hd"] / f"{name}.png"
        master_img.save(master_path, format="PNG")
        results["master_hd"].append(master_path)

    # Also generate LINE Main icon (240x240) and Tab icon (96x74) using the first sticker
    if sticker_paths:
        first_img = Image.open(sticker_paths[0]).convert("RGBA")
        main_icon = fit_to_box(first_img, 240, 240, padding=10, expand_canvas=True)
        main_icon.save(dirs["line"] / "main.png", format="PNG")

        tab_icon = fit_to_box(first_img, 96, 74, padding=4, expand_canvas=True)
        tab_icon.save(dirs["line"] / "tab.png", format="PNG")

    return results


def create_montage_preview(
    sticker_paths: List[Path],
    output_path: Path,
    title: str = "Chat Sticker Collection",
    labels: Optional[List[str]] = None,
    cols: int = 3,
    cell_size: int = 320,
    background_theme: str = "aesthetic",
) -> Path:
    """
    Assemble all processed stickers into a stylish showcase poster/montage.
    """
    num_items = len(sticker_paths)
    if num_items == 0:
        raise ValueError("No sticker images provided for montage.")

    rows = math.ceil(num_items / cols)

    header_h = 100
    footer_h = 40
    padding = 24
    grid_w = cols * cell_size + (cols + 1) * padding
    grid_h = rows * cell_size + (rows + 1) * padding

    total_w = grid_w
    total_h = header_h + grid_h + footer_h

    # Aesthetic modern pastel gradient or clean dark/light canvas
    if background_theme == "aesthetic":
        # Soft cozy gradient
        canvas = Image.new("RGB", (total_w, total_h), (245, 247, 250))
        draw = ImageDraw.Draw(canvas)
        # Subtle horizontal soft gradient
        for y in range(total_h):
            ratio = y / total_h
            r = int(246 * (1 - ratio) + 238 * ratio)
            g = int(248 * (1 - ratio) + 242 * ratio)
            b = int(252 * (1 - ratio) + 250 * ratio)
            draw.line([(0, y), (total_w, y)], fill=(r, g, b))
    else:
        canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

    # Load CJK fonts
    cjk_font_paths = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\mingliu.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    title_font = None
    label_font = None
    for fp in cjk_font_paths:
        if os.path.exists(fp):
            try:
                title_font = ImageFont.truetype(fp, 34)
                label_font = ImageFont.truetype(fp, 18)
                break
            except Exception:
                pass

    if not title_font:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    # Header title
    draw.text(
        (padding + 10, 32),
        title,
        font=title_font,
        fill=(30, 41, 59),
    )

    # Sticker cards
    for idx, path in enumerate(sticker_paths):
        r = idx // cols
        c = idx % cols

        x = padding + c * (cell_size + padding)
        y = header_h + padding + r * (cell_size + padding)

        # Draw cute soft white card background for each sticker
        card_box = [x, y, x + cell_size, y + cell_size]
        draw.rounded_rectangle(card_box, radius=18, fill=(255, 255, 255), outline=(226, 232, 240), width=1)

        # Fit sticker inside card
        img = Image.open(path).convert("RGBA")
        inner_sticker = fit_to_box(img, cell_size - 32, cell_size - 56, padding=4, expand_canvas=False)

        paste_x = x + (cell_size - inner_sticker.width) // 2
        paste_y = y + 16 + (cell_size - 56 - inner_sticker.height) // 2
        canvas.paste(inner_sticker, (paste_x, paste_y), inner_sticker)

        # Label tag at bottom of card
        label_text = labels[idx] if labels and idx < len(labels) else path.stem.split("_", 1)[-1]
        draw.text(
            (x + 18, y + cell_size - 34),
            f"#{idx+1} {label_text}",
            font=label_font,
            fill=(100, 116, 139),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Process stickers from sprite sheet or images.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: slice
    slice_parser = subparsers.add_parser("slice", help="Slice a grid sheet into stickers.")
    slice_parser.add_argument("--sheet", type=Path, required=True, help="Path to raw sprite sheet PNG.")
    slice_parser.add_argument("--rows", type=int, default=3, help="Number of rows (default: 3).")
    slice_parser.add_argument("--cols", type=int, default=3, help="Number of cols (default: 3).")
    slice_parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for sliced stickers.")
    slice_parser.add_argument("--no-chroma", action="store_true", help="Disable magenta chroma-key removal.")
    slice_parser.add_argument("--no-border", action="store_true", help="Disable die-cut white border.")
    slice_parser.add_argument("--border-width", type=int, default=12, help="Die-cut white border width in px.")
    slice_parser.add_argument("--labels", nargs="*", default=None, help="Optional text labels for each sticker.")
    slice_parser.add_argument("--export-packages", action="store_true", help="Also export LINE/Telegram/WeChat packages.")
    slice_parser.add_argument("--montage", action="store_true", help="Also generate showcase montage preview.")

    # Subcommand: export
    export_parser = subparsers.add_parser("export", help="Export existing sticker images to platform packages.")
    export_parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing sticker PNGs.")
    export_parser.add_argument("--output-dir", type=Path, required=True, help="Directory to export packages.")
    export_parser.add_argument("--montage", action="store_true", help="Also generate montage preview.")

    args = parser.parse_args()

    if args.command == "slice":
        print(f"Slicing sheet {args.sheet} ({args.rows}x{args.cols})...")
        sliced = slice_grid_sheet(
            sheet_path=args.sheet,
            rows=args.rows,
            cols=args.cols,
            output_dir=args.output_dir / "raw_sliced",
            labels=args.labels,
            chroma_key=not args.no_chroma,
            add_border=not args.no_border,
            border_width=args.border_width,
        )
        print(f"Successfully sliced {len(sliced)} stickers to {args.output_dir / 'raw_sliced'}")

        if args.export_packages:
            print("Packaging for LINE, Telegram, Discord, and WeChat...")
            packages = export_platform_packages(sliced, args.output_dir / "packages", labels=args.labels)
            for pkg, files in packages.items():
                print(f"  - {pkg}: {len(files)} files")

        if args.montage:
            montage_file = args.output_dir / "sticker_montage_preview.png"
            create_montage_preview(sliced, montage_file, labels=args.labels, cols=args.cols)
            print(f"Showcase montage saved to: {montage_file}")

    elif args.command == "export":
        input_files = sorted(list(args.input_dir.glob("*.png")))
        if not input_files:
            print(f"No PNG files found in {args.input_dir}")
            sys.exit(1)
        print(f"Packaging {len(input_files)} sticker files...")
        packages = export_platform_packages(input_files, args.output_dir)
        for pkg, files in packages.items():
            print(f"  - {pkg}: {len(files)} files")

        if args.montage:
            montage_file = args.output_dir / "sticker_montage_preview.png"
            create_montage_preview(input_files, montage_file)
            print(f"Showcase montage saved to: {montage_file}")


if __name__ == "__main__":
    main()
