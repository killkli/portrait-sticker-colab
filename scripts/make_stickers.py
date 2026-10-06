#!/usr/bin/env python3
"""
End-to-End Portrait Sticker Generator (All-in-One CLI).
Automates the full pipeline:
1. Feature extraction & Manifest building (manifest_builder.py)
2. Qwen-Image-2.1 Colab execution (runner.py)
3. Sprite post-processing, die-cut borders, multi-platform packaging (sticker_processor.py)
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"


def to_wsl_path(path: Path | str) -> str:
    """Convert Windows path to WSL /mnt/... path if needed."""
    p_str = str(Path(path).resolve())
    if len(p_str) >= 2 and p_str[1] == ":":
        drive = p_str[0].lower()
        rest = p_str[2:].replace("\\", "/")
        return f"/mnt/{drive}{rest}"
    return p_str.replace("\\", "/")


def run_command(cmd: list[str] | str, shell: bool = False) -> None:
    print(f"Executing: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    result = subprocess.run(cmd, shell=shell, check=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")


def main():
    parser = argparse.ArgumentParser(description="End-to-end portrait sticker pack generator.")
    parser.add_argument("--photo", type=str, required=True, help="Path to source portrait photo.")
    parser.add_argument(
        "--style",
        type=str,
        default="pop_mart_3d",
        choices=["chibi", "pop_mart_3d", "retro_comic", "pixel_art", "meme", "korean_pastel", "fauvism"],
        help="Sticker art style.",
    )
    parser.add_argument("--layout", type=str, default="3x3", choices=["3x3", "2x4"], help="Grid layout (3x3 or 2x4).")
    parser.add_argument("--lang", type=str, default="zh-TW", choices=["zh-TW", "en", "none"], help="Text label language.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for generated sticker pack.")
    parser.add_argument("--gpu", type=str, default="L4", choices=["L4", "A100"], help="Colab GPU accelerator.")
    parser.add_argument("--border-width", type=int, default=8, help="Die-cut white border width in px.")

    args = parser.parse_args()

    photo_path = Path(args.photo).resolve()
    if not photo_path.exists():
        print(f"Error: Photo not found: {photo_path}")
        sys.exit(1)

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = out_dir / "_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Manifest building
    manifest_path = work_dir / "jobs.json"
    print("\n[Step 1/3] Building Qwen-Image-2.1 prompt manifest...")
    manifest_builder_script = SCRIPTS_DIR / "manifest_builder.py"
    
    # Check if WSL path needed for runner
    is_windows = platform.system() == "Windows"
    runner_photo_path = to_wsl_path(photo_path) if is_windows else str(photo_path)

    run_command([
        sys.executable,
        str(manifest_builder_script),
        "--photo", runner_photo_path,
        "--style", args.style,
        "--layout", args.layout,
        "--lang", args.lang,
        "--output", str(manifest_path),
    ])

    # 2. Diffusion generation on Colab
    print(f"\n[Step 2/3] Generating {args.style} sticker sheet on Google Colab ({args.gpu})...")
    colab_output_dir = work_dir / "colab_output"
    colab_output_dir.mkdir(parents=True, exist_ok=True)

    runner_script = SCRIPTS_DIR / "runner.py"
    if is_windows:
        wsl_runner = to_wsl_path(runner_script)
        wsl_manifest = to_wsl_path(manifest_path)
        wsl_out = to_wsl_path(colab_output_dir)
        cmd = f'wsl -d ubuntu bash -lc "python3 {wsl_runner} batch --manifest {wsl_manifest} --gpu {args.gpu} --high-mem --output-dir {wsl_out} --stop-on-complete"'
        run_command(cmd, shell=True)
    else:
        cmd = [
            sys.executable,
            str(runner_script),
            "batch",
            "--manifest", str(manifest_path),
            "--gpu", args.gpu,
            "--high-mem",
            "--output-dir", str(colab_output_dir),
            "--stop-on-complete",
        ]
        run_command(cmd)

    # Find the output png
    sheet_files = list(colab_output_dir.glob("*.png"))
    if not sheet_files:
        print(f"Error: No generated PNG found in {colab_output_dir}")
        sys.exit(1)
    sheet_file = sheet_files[0]
    print(f"Generated raw sheet: {sheet_file}")

    # 3. Postprocessing
    print("\n[Step 3/3] Slicing grid, removing chroma background, adding die-cut borders, and packaging...")
    rows = 3 if args.layout == "3x3" else 2
    cols = 3 if args.layout == "3x3" else 4

    labels = [
        "嗨！ (Hello)",
        "OK啦！ (OK)",
        "謝謝泥 (Thanks)",
        "笑死！ (LOL)",
        "嗚嗚嗚 (Cry)",
        "氣炸！ (Angry)",
        "愛你唷 (Love)",
        "晚安安 (Goodnight)",
    ]
    if args.layout == "3x3":
        labels.append("蛤？？ (What)")

    processor_script = SCRIPTS_DIR / "sticker_processor.py"
    run_command([
        sys.executable,
        str(processor_script),
        "slice",
        "--sheet", str(sheet_file),
        "--rows", str(rows),
        "--cols", str(cols),
        "--output-dir", str(out_dir),
        "--border-width", str(args.border_width),
        "--export-packages",
        "--montage",
        "--labels", *labels,
    ])

    print("\n🎉 Sticker Pack Generated Successfully!")
    print(f"📁 Packages: {out_dir / 'packages'}")
    print(f"🖼️ Showcase Montage: {out_dir / 'sticker_montage_preview.png'}")


if __name__ == "__main__":
    main()
