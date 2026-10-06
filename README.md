# 🎨 Portrait Sticker Colab (人像照片轉聊天表情貼圖 - Colab 專用版)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Model: Qwen-Image-2.1](https://img.shields.io/badge/Model-Qwen--Image--2.1-orange.svg)](https://github.com/QwenLM)
[![Platform: Colab L4/A100](https://img.shields.io/badge/Backend-Google_Colab-yellow.svg)](https://colab.research.google.com/)

將任意真實人像照片自動轉換為通訊軟體專用的一整組聊天表情貼圖（支援 **LINE、Telegram、Discord、微信、WhatsApp**）。

本專案為完全獨立封裝的 AI 貼圖生成引擎，採用 **Google Colab GPU（L4 / A100）** 調度阿里巴巴旗艦級開源多模態擴散模型 **Qwen-Image-2.1**，結合 Sprite 多宮格單次生成技術與本地端抗鋸齒去背、實體貼圖白邊裁切線（Die-Cut Border）後製引擎。

---

## ✨ 核心特色 (Key Features)

- **🎭 肖像神韻高度還原（Identity Anchors）**：在卡通化與風格化的同時，牢牢鎖定個人標誌特徵（黑框眼鏡、髮型、眼眸神韻、招牌笑容）。
- **⚡ 3x3 九宮格極速省算力**：採用 Sprite 多宮格洋紅底（`#FF00FF`）單次生成策略，只需一次 Colab 任務（數分鐘），即可產出整組 9 張表情，人物造型與色調 100% 統一。
- **✂️ 專業實體貼圖白邊（Die-Cut Border）**：自動去除洋紅背景，沿著人物邊緣自動生成 8~12px 平滑純白裁切線與立體微投影，在深色或淺色聊天視窗皆具備極佳辨識度。
- **📦 全平台官方規格自動打包**：
  - **LINE 貼圖**：符合最大 370×320 px 規範，包含必備的 `main.png`（240×240 封面大圖）與 `tab.png`（96×74 聊天分頁小圖）。
  - **Telegram / Discord / WhatsApp**：512×512 px 高解析度透明圖檔。
  - **微信表情包**：240×240 px 輕量級透明 PNG。
  - **超清典藏母檔**：1024×1024 px 原生母檔。
- **🖼️ 全套展示海報自動生成**：自動合成為精美的整套貼圖展示海報（Montage Showcase）。

---

## 🎨 內建 7 大熱門風格 (Built-in Styles)

1. **`pop_mart_3d` (3D 盲盒公仔風)**：泡泡瑪特潮玩質感、軟陶黏土溫潤光澤、微縮 3D 黑框眼鏡、柔光箱立體棚拍感。
2. **`fauvism` (野獸派狂野風格)**：馬蒂斯與德蘭式的大膽撞色（朱紅、鈷藍、鎘黃、翠綠）、狂放藝術筆觸、張力十足。
3. **`chibi` (日系 Q 版萌系)**：2 頭身大頭小身、水汪汪大眼、粉嫩腮紅，經典可愛動漫周邊感（類似卡娜赫拉）。
4. **`retro_comic` (美式復古漫畫/普普風)**：粗黑輪廓墨線、班戴網點陰影、高對比原色、美漫狀聲詞對話框。
5. **`pixel_art` (經典 2D 像素風)**：16-bit 點陣像素表情包、懷舊 JRPG 遊戲頭像與表情符號。
6. **`meme` (搞笑魔性顏藝)**：誇張五官變形、爆笑肢體動作、草根塗鴉線條、LINE 爆笑迷因感。
7. **`korean_pastel` (韓系簡約手繪)**：簡約流暢鋼筆線條、低飽和馬卡龍粉彩色調、溫柔文青插畫。

---

## 🚀 快速開始 (Quick Start)

### 1. 環境需求
- Python 3.10+
- 安裝基本依賴：
  ```bash
  pip install pillow
  ```
- Google Colab CLI 已認證授權（具備運算單元額度，如 L4 或 A100 GPU）。
- Windows 建議使用 WSL (Ubuntu) 環境執行。

### 2. 一鍵生成全套貼圖 (All-in-One CLI)

```bash
python scripts/make_stickers.py \
  --photo "/path/to/your_photo.jpg" \
  --style "pop_mart_3d" \
  --layout "3x3" \
  --gpu "L4" \
  --output-dir "./output_stickers"
```

參數說明：
- `--photo`：輸入人像照片路徑。
- `--style`：貼圖風格（`pop_mart_3d`、`fauvism`、`chibi`、`retro_comic`、`pixel_art`、`meme`、`korean_pastel`）。
- `--layout`：`3x3`（9 入組）或 `2x4`（8 入組）。
- `--gpu`：Colab GPU 加速器（預設 `L4`，支援 `A100`）。
- `--border-width`：實體白邊寬度（預設 `8` px）。

---

## 📁 輸出目錄結構 (Output Structure)

```
output_stickers/
├── raw_sliced/                     # 9 張透明底、帶實體白邊的獨立貼圖 PNG
│   ├── 01_嗨.png
│   └── ...
├── packages/
│   ├── line_370x320/              # LINE 貼圖官方標準規格 (含 main.png 封面與 tab.png 分頁圖)
│   ├── telegram_discord_512x512/  # Telegram / Discord / WhatsApp 512x512 高清貼圖
│   ├── wechat_240x240/            # 微信表情包規格
│   └── master_hd_1024x1024/       # 1024x1024 超清母檔
└── sticker_montage_preview.png     # 整套 9 入貼圖展示預覽海報
```

---

## 🧩 模組分步單獨執行

各模組亦可獨立分步調度：

1. **產生 Prompt 任務清單**：
   ```bash
   python scripts/manifest_builder.py --photo "photo.jpg" --style "fauvism" --layout "3x3" --output "jobs.json"
   ```
2. **調用 Colab 算力執行生成**：
   ```bash
   python scripts/runner.py batch --manifest jobs.json --gpu L4 --high-mem --output-dir ./colab_out --stop-on-complete
   ```
3. **本地切片、去背與打包**：
   ```bash
   python scripts/sticker_processor.py slice --sheet ./colab_out/sheet.png --rows 3 --cols 3 --output-dir ./stickers --export-packages --montage
   ```

---

## 📄 開源授權 (License)

本專案採用 [MIT License](LICENSE) 授權。
