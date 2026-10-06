# 通訊軟體表情貼圖格式規範 (Chat App Sticker Specifications)

本文件列出主流通訊軟體上架與匯入貼圖所需的標準解析度、色彩與檔案限制。`sticker_processor.py` 會自動導出完全符合這些規範的貼圖包。

---

## 1. LINE 貼圖 (LINE Stickers)
- **貼圖圖片 (Stickers)**：
  - 格式：PNG（RGB / RGBA 透明背景）
  - 尺寸：最大寬 370 px × 最大高 320 px（保持比例，四周保留至少 10 px 安全留白）
  - 數量：8 / 16 / 24 / 32 / 40 張
- **主要圖片 (Main Image)**：
  - 尺寸：240 × 240 px
- **標籤圖片 (Chat Tab Icon)**：
  - 尺寸：96 × 74 px

---

## 2. Telegram 貼圖 (Telegram Stickers)
- **靜態貼圖 (Static)**：
  - 格式：PNG 或 WebP（透明背景）
  - 尺寸：精確 512 × 512 px（一邊固定為 512 px，另一邊不大於 512 px）
  - 大小限制：小於 512 KB
  - 特色：強烈建議加上白色描邊（Stroke）與微陰影，以利在深色/淺色主題中清晰辨識。

---

## 3. Discord 貼圖與表情符號 (Discord Stickers & Emotes)
- **自訂貼圖 (Custom Stickers)**：
  - 尺寸：320 × 320 px（推薦 512 × 512 px 自動縮圖）
  - 格式：PNG / APNG
  - 大小限制：小於 512 KB
- **Emoji 自訂表情**：
  - 尺寸：128 × 128 px（PNG 透明）

---

## 4. 微信表情包 (WeChat Stickers)
- **貼圖主圖**：
  - 尺寸：240 × 240 px（PNG 透明背景）
  - 檔案大小：小於 100 KB
  - 數量：單套 8 / 16 / 24 張
- **橫幅與圖示**：
  - 封面圖：240 × 240 px
  - 聊天面板圖標：50 × 50 px

---

## 5. WhatsApp 貼圖 (WhatsApp Stickers)
- **貼圖格式**：WebP 或 PNG（透明背景）
- **尺寸**：精確 512 × 512 px
- **邊距**：每邊至少 16 px 留白
- **大小限制**：小於 100 KB
