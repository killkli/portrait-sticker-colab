---
name: portrait-sticker-colab
description: 使用 Google Colab GPU (Qwen-Image-2.1) 將人像照片轉換為通訊軟體專用的一整組聊天表情貼圖（LINE、Telegram、Discord、微信、WhatsApp）。完全獨立運作，內建 Qwen-Image-2.1 Colab 算力調度、人物特徵錨定、多風格切換、Sprite 格狀切分、洋紅去背、實體貼圖白邊裁切線 (Die-Cut Border) 與多平台規格導出。
---

# Portrait Sticker Colab (人像照片轉聊天表情貼圖 - Colab 專用版)

本 Skill 為**100% 完全獨立運作（Zero External Skill Dependencies）**的表情貼圖全流程引擎。只需輸入一張人像照片，即可自動轉換為高品質、神韻精準、風格統一的整組聊天軟體表情貼圖包（支援 LINE、Telegram、Discord、微信、WhatsApp 等）。

---

## 核心亮點與完全獨立架構

- **零外部技能依賴**：內建完整的 Qwen-Image-2.1 Colab 調度腳本（`scripts/runner.py`）與專用 Notebook 資產（`assets/Qwen_Image_2_1_Colab.ipynb`），無需安裝任何其他技能即可直接調用雲端 GPU 算力。
- **一鍵端到端 CLI (`make_stickers.py`)**：整合「人像分析 ➔ 生成 Manifest ➔ 雲端 GPU 算力運算 ➔ 貼圖切分去背 ➔ 實體白邊裁切線 ➔ 多平台打包與展示海報」，一條指令全自動完成。
- **精確人像特徵鎖定（Identity Anchors）**：在風格化（Q 版、3D、漫畫）的同時，牢牢鎖定髮型、眼鏡、臉型輪廓與招牌表情神韻。
- **九宮格極速省算力策略**：採用多宮格（3x3 或 2x4）洋紅背景（`#FF00FF`）單次生成技術，幾分鐘內產出全套貼圖，風格與面貌 100% 統一。
- **專業級實體貼圖白邊（Die-Cut Border）**：自動生成 8~12px 乾淨的實體白邊與微立體陰影，貼在任何淺色/深色聊天背景都極為清晰醒目。

---

## 核心工作流程 (5-Stage Workflow)

```
[使用者上傳照片] ──▶ 1. 人像特徵解析 (髮型、眼鏡、服飾、神韻)
                         │
                         ▼
                     2. 提供風格選單 (互動引導使用者選擇)
                         │
                         ▼
                     3. 表情動作規劃 (預設 9 宮格或 8/16 入組)
                         │
                         ▼
                     4. 內建 Qwen-Image-2.1 引擎生成 (Grid Sheet / Batch)
                         │
                         ▼
                     5. 專屬 Sprite 後製切分與貼圖包規格化
                         ├─ 洋紅自動去背 (Chroma-Key Removal)
                         ├─ 實體白邊裁切線 (Die-Cut White Border + Shadow)
                         ├─ 規格適配 (LINE 370x320, TG/Discord 512x512, WeChat 240x240)
                         └─ 全套展示海報 (Montage Showcase)
```

---

## 一鍵全自動指令 (All-in-One CLI)

最推薦的使用方式，只要一行指令即可自動完成所有步驟：

```bash
python ~/.gemini/config/skills/portrait-sticker-maker/scripts/make_stickers.py \
  --photo "/path/to/user_photo.jpg" \
  --style "pop_mart_3d" \
  --layout "3x3" \
  --output-dir "./output_stickers"
```

參數說明：
- `--photo`：使用者人像照片路徑。
- `--style`：貼圖風格（`chibi`、`pop_mart_3d`、`fauvism`、`retro_comic`、`pixel_art`、`meme`、`korean_pastel`）。
- `--layout`：`3x3`（9 入組）或 `2x4`（8 入組）。
- `--gpu`：Colab GPU 加速器（預設 `L4`，支援 `A100`）。
- `--border-width`：實體白邊寬度（預設 `8` px）。

---

## 支援風格庫 (Styles)

1. **✨ 3D 盲盒公仔 (`pop_mart_3d`)**：泡泡瑪特潮玩公仔、軟陶黏土溫潤光澤、柔光箱棚拍立體光影，精緻手辦風。
2. **🔥 野獸派狂野風格 (`fauvism`)**：馬蒂斯與德蘭式的大膽撞色（朱紅、鈷藍、鎘黃、翠綠）、狂放藝術筆觸、張力十足。
3. **🧸 日系 Q 版萌系 (`chibi`)**：大頭小身 2 頭身、水汪汪大眼、粉嫩腮紅，經典可愛動漫周邊感（類似卡娜赫拉）。
4. **💥 美式復古漫畫/普普風 (`retro_comic`)**：粗黑輪廓墨線、班戴網點陰影、高對比原色、美漫狀聲詞對話框。
5. **👾 經典 2D 像素風 (`pixel_art`)**：16-bit 點陣像素表情包、懷舊 JRPG 遊戲頭像與表情符號。
6. **🤪 搞笑魔性顏藝 (`meme`)**：誇張五官變形、爆笑肢體動作、草根塗鴉線條、LINE 爆笑迷因感。
7. **🌿 韓系簡約手繪 (`korean_pastel`)**：簡約流暢鋼筆線條、低飽和馬卡龍粉彩色調、溫柔文青插畫。

---

## 分步獨立工具說明

除了 `make_stickers.py` 一鍵腳本外，各模組亦可獨立單獨執行：

### 1. 產生生圖清單 (`scripts/manifest_builder.py`)
```bash
python scripts/manifest_builder.py \
  --photo "/path/to/photo.jpg" \
  --style "pop_mart_3d" \
  --layout "3x3" \
  --output "jobs.json"
```

### 2. 本技能內建 Colab 調度 (`scripts/runner.py`)
```bash
# 透過 WSL Ubuntu 執行：
wsl -d ubuntu bash -lc "python3 ~/.gemini/config/skills/portrait-sticker-maker/scripts/runner.py batch --manifest jobs.json --gpu L4 --high-mem --output-dir ./colab_output --stop-on-complete"
```

### 3. 切片、去背、白邊與平台轉檔 (`scripts/sticker_processor.py`)
```bash
python scripts/sticker_processor.py slice \
  --sheet ./colab_output/sheet.png \
  --rows 3 --cols 3 \
  --output-dir ./stickers \
  --border-width 10 \
  --export-packages \
  --montage
```

---

## 輸出成品目錄結構

執行完畢後產出標準化貼圖包：

```
output_dir/
├── raw_sliced/                     # 獨立透明帶白邊貼圖 PNG
│   ├── 01_嗨.png
│   └── ...
├── packages/
│   ├── line_370x320/              # LINE 貼圖官方標準規格 (含 main.png 封面與 tab.png 分頁圖)
│   ├── telegram_discord_512x512/  # Telegram / Discord / WhatsApp 512x512 高清貼圖
│   ├── wechat_240x240/            # 微信表情包規格
│   └── master_hd_1024x1024/       # 1024x1024 超清母檔
└── sticker_montage_preview.png     # 整套貼圖展示預覽海報
```

---

## 相關參考資源

- [`references/styles.md`](file:///C:/Users/g1060/.gemini/config/skills/portrait-sticker-maker/references/styles.md)：7 大風格 Prompt 配方與視覺範例。
- [`references/expressions.md`](file:///C:/Users/g1060/.gemini/config/skills/portrait-sticker-maker/references/expressions.md)：常用貼圖表情動作庫與中英文對照。
- [`references/specs.md`](file:///C:/Users/g1060/.gemini/config/skills/portrait-sticker-maker/references/specs.md)：LINE、Telegram、Discord、微信貼圖官方規格規範。
