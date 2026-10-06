#!/usr/bin/env python3
"""
Manifest Builder for Portrait-Sticker-Maker Skill.
Generates jobs.json for qwen-image-colab to generate stickers using Alibaba Qwen-Image-2.1.
Supports Grid Sheet Mode (single-job 3x3 / 2x4) and Batch Mode (individual sticker jobs).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

# Standard Style Definitions
STYLES: Dict[str, Dict[str, str]] = {
    "chibi": {
        "name": "日系 Q 版萌系 (Chibi Anime)",
        "prompt_prefix": (
            "Ultra-cute 2D Chibi anime character sticker design, "
            "based on the facial features, hairstyle, and likeness of the person in <Picture 1>. "
            "2-head-tall proportions, adorable oversized head, cute expressive eyes, soft rosy blush, "
            "clean vector-like outlines, vibrant cell shading, die-cut sticker aesthetics. "
        ),
    },
    "pop_mart_3d": {
        "name": "3D 盲盒公仔 (Pop Mart / Clay 3D)",
        "prompt_prefix": (
            "Trendy 3D vinyl toy figurine sticker, Pop Mart style, blind box collectible character, "
            "faithfully stylized based on the person in <Picture 1>. "
            "Smooth soft clay texture, warm studio softbox lighting, glossy eye reflection, "
            "miniature chibi toy proportions, clean physical die-cut sticker look. "
        ),
    },
    "retro_comic": {
        "name": "美式復古漫畫/普普風 (Retro Comic / Pop-Art)",
        "prompt_prefix": (
            "Vintage American comic book sticker illustration, 1960s pop-art Lichtenstein style, "
            "stylized portrait based on the person in <Picture 1>. "
            "Heavy bold ink outlines, halftone Ben-Day dots shading, bold primary color palette, "
            "dynamic retro comic speech bubbles, sticker graphic aesthetics. "
        ),
    },
    "pixel_art": {
        "name": "經典 2D 像素風 (16-bit Pixel Art Sprite)",
        "prompt_prefix": (
            "Nostalgic 16-bit pixel art character sprite sticker, retro JRPG chat emote style, "
            "capturing key recognizable features from the person in <Picture 1>. "
            "Crisp chunky pixel clusters, vibrant retro color palette, expressive retro arcade emote poses, "
            "game UI sticker aesthetics. "
        ),
    },
    "meme": {
        "name": "搞笑魔性顏藝 (Meme / Dramatic Expression)",
        "prompt_prefix": (
            "Humorous, funny exaggerated cartoon meme sticker, LINE sticker meme culture style, "
            "caricature based on the person in <Picture 1>. "
            "Hilarious exaggerated facial expressions, funny dynamic body comedy gestures, "
            "hand-drawn doodle lines, playful anime reaction face sticker aesthetics. "
        ),
    },
    "korean_pastel": {
        "name": "韓系簡約手繪 (Korean Line & Pastel)",
        "prompt_prefix": (
            "Minimalist Korean warm line-drawing sticker, cozy lifestyle aesthetic, "
            "delicate stylized illustration of the person in <Picture 1>. "
            "Smooth continuous pen lines, soothing muted pastel watercolor fills, charming gentle vibe, "
            "aesthetic daily chat sticker look. "
        ),
    },
    "fauvism": {
        "name": "野獸派狂野風格 (Fauvism Wild Expression)",
        "prompt_prefix": (
            "Wild Fauvism modern chat sticker illustration, inspired by Henri Matisse and André Derain. "
            "Bold, expressive, wild, and spontaneous brushstrokes, vibrant saturated clashing colors "
            "(fiery vermilion red, bright cadmium yellow, electric cobalt blue, wild emerald green, deep violet contours). "
            "Artistic, highly expressive character caricature capturing the recognizable facial features of the person in <Picture 1>. "
            "Dynamic thick artistic outlines, raw painterly brush textures, energetic and passionate emotional expression, modern pop-art chat sticker aesthetics. "
        ),
    },
}

# Standard 9-Sticker Expression Matrix (for 3x3 Grid)
EXPRESSIONS_3X3: List[Dict[str, str]] = [
    {
        "id": "hello",
        "action": "waving cheerfully with a warm happy smile, welcoming gesture",
        "text_zh": "嗨！",
        "text_en": "HELLO!",
    },
    {
        "id": "ok_thumbs_up",
        "action": "giving a confident double thumbs-up with an encouraging wink",
        "text_zh": "OK啦！",
        "text_en": "OK!",
    },
    {
        "id": "thank_you",
        "action": "clasping hands together in sincere gratitude with sparkling eyes",
        "text_zh": "謝謝泥",
        "text_en": "THANKS!",
    },
    {
        "id": "lol_laugh",
        "action": "holding belly laughing out loud with tears of joy, wide hilarious open-mouth grin",
        "text_zh": "哈哈哈",
        "text_en": "LOL!",
    },
    {
        "id": "crying_sad",
        "action": "comical waterfall streams of tears flowing from eyes, sobbing with pouty mouth",
        "text_zh": "嗚嗚嗚",
        "text_en": "NOOO!",
    },
    {
        "id": "angry_rage",
        "action": "fuming with anger, steam blowing from ears, red flushed face with comical rage vein",
        "text_zh": "氣炸！",
        "text_en": "ANGRY!",
    },
    {
        "id": "love_heart",
        "action": "blowing sweet finger-hearts or hugging a giant glowing red heart, blushing cheeks",
        "text_zh": "愛你唷",
        "text_en": "LOVE YOU",
    },
    {
        "id": "sleepy_goodnight",
        "action": "wrapped in a cozy blanket with sleepy eyes, drooling slightly, floating 'Zzz' bubbles",
        "text_zh": "晚安安",
        "text_en": "GOODNIGHT",
    },
    {
        "id": "confused_question",
        "action": "tilting head quizzically scratching head with giant floating question marks '???'",
        "text_zh": "蛤？？",
        "text_en": "WHAT?!",
    },
]

# Standard 8-Sticker Expression Matrix (for 2x4 Grid)
EXPRESSIONS_2X4 = EXPRESSIONS_3X3[:8]


def build_grid_prompt(
    style_key: str,
    layout: str = "3x3",
    lang: str = "zh-TW",
    custom_desc: str = "",
) -> str:
    style_info = STYLES.get(style_key, STYLES["chibi"])
    expressions = EXPRESSIONS_3X3 if layout == "3x3" else EXPRESSIONS_2X4

    rows = 3 if layout == "3x3" else 2
    cols = 3 if layout == "3x3" else 4
    total = rows * cols

    items_text = []
    for idx, expr in enumerate(expressions):
        text_badge = ""
        if lang == "zh-TW" and expr.get("text_zh"):
            text_badge = f' with cute sticker text "{expr["text_zh"]}"'
        elif lang == "en" and expr.get("text_en"):
            text_badge = f' with cute sticker text "{expr["text_en"]}"'

        items_text.append(f"Cell {idx+1}: {expr['action']}{text_badge}")

    actions_joined = "; ".join(items_text)

    prompt = (
        f"{style_info['prompt_prefix']}"
        f"{custom_desc + ' ' if custom_desc else ''}"
        f"A multi-panel sticker sheet containing EXACTLY {total} distinct emoji stickers arranged in a {rows}x{cols} grid ({rows} rows, {cols} columns). "
        f"The subject must stay completely identical to the character identity in <Picture 1> across every cell. "
        f"Specific expressions for each cell in order: {actions_joined}. "
        f"ABSOLUTE RULES: "
        f"1. SOLID FLAT MAGENTA (#FF00FF) background everywhere between cells, NO gradients, NO shadows on background. "
        f"2. Each sticker character is neatly centered inside its grid cell with generous margin around it. "
        f"3. No body parts or text crossing cell boundaries. "
        f"4. Distinct, high-contrast, cute sticker look ready for chat apps."
    )
    return prompt


def generate_manifest(
    photo_path: str,
    output_manifest: Path,
    style_key: str = "chibi",
    layout: str = "3x3",
    mode: str = "grid",
    lang: str = "zh-TW",
    custom_desc: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 40,
) -> Dict[str, Any]:
    photo_abs = str(Path(photo_path).resolve())

    if mode == "grid":
        prompt = build_grid_prompt(
            style_key=style_key,
            layout=layout,
            lang=lang,
            custom_desc=custom_desc,
        )
        jobs = [
            {
                "id": f"sticker_sheet_{layout}_{style_key}",
                "mode": "edit",
                "reference_images": [photo_abs],
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "output_name": f"sticker_sheet_{layout}_{style_key}",
            }
        ]
    else:
        # Individual sticker batch mode
        style_info = STYLES.get(style_key, STYLES["chibi"])
        expressions = EXPRESSIONS_3X3 if layout == "3x3" else EXPRESSIONS_2X4
        jobs = []

        for idx, expr in enumerate(expressions):
            text_badge = ""
            if lang == "zh-TW" and expr.get("text_zh"):
                text_badge = f' with cute sticker text "{expr["text_zh"]}"'
            elif lang == "en" and expr.get("text_en"):
                text_badge = f' with cute sticker text "{expr["text_en"]}"'

            single_prompt = (
                f"{style_info['prompt_prefix']}"
                f"{custom_desc + ' ' if custom_desc else ''}"
                f"Single chat sticker of the person in <Picture 1>, performing: {expr['action']}{text_badge}. "
                f"Full character body/upper-body centered with generous margin, solid flat magenta (#FF00FF) background, "
                f"die-cut sticker border, no edge clipping, high contrast."
            )
            jobs.append(
                {
                    "id": f"sticker_{idx+1:02d}_{expr['id']}",
                    "mode": "edit",
                    "reference_images": [photo_abs],
                    "prompt": single_prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "output_name": f"sticker_{idx+1:02d}_{expr['id']}",
                }
            )

    manifest_data = {
        "metadata": {
            "source_photo": photo_abs,
            "style": style_key,
            "style_name": STYLES.get(style_key, {}).get("name", style_key),
            "layout": layout,
            "mode": mode,
            "lang": lang,
        },
        "jobs": jobs,
    }

    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_data


def main():
    parser = argparse.ArgumentParser(description="Build Qwen-Image-2.1 Colab manifest for sticker generation.")
    parser.add_argument("--photo", type=str, required=True, help="Path to input portrait photo.")
    parser.add_argument(
        "--style",
        type=str,
        default="chibi",
        choices=list(STYLES.keys()),
        help=f"Sticker art style (choices: {', '.join(STYLES.keys())})",
    )
    parser.add_argument("--layout", type=str, default="3x3", choices=["3x3", "2x4"], help="Grid layout (3x3=9 stickers, 2x4=8 stickers).")
    parser.add_argument("--mode", type=str, default="grid", choices=["grid", "batch"], help="grid (1 sheet) or batch (individual).")
    parser.add_argument("--lang", type=str, default="zh-TW", choices=["zh-TW", "en", "none"], help="Text label language.")
    parser.add_argument("--custom-desc", type=str, default="", help="Additional details to retain (e.g. glasses, brown curly hair).")
    parser.add_argument("--output", type=Path, default=Path("jobs.json"), help="Output manifest JSON path.")
    parser.add_argument("--steps", type=int, default=40, help="Sampling steps (default: 40).")

    args = parser.parse_args()

    manifest = generate_manifest(
        photo_path=args.photo,
        output_manifest=args.output,
        style_key=args.style,
        layout=args.layout,
        mode=args.mode,
        lang=args.lang,
        custom_desc=args.custom_desc,
        steps=args.steps,
    )
    print(f"Generated manifest with {len(manifest['jobs'])} jobs to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
