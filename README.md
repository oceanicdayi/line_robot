---
title: LINE Earthquake Bot
sdk: docker
app_port: 7860
---


# LINE 多功能地震資訊與 AI 助理機器人

這是一個部署在 Hugging Face Spaces 上的多功能 LINE Bot。它整合了來自台灣中央氣象署 (CWA) 和美國地質調查局 (USGS) 的地震資訊，並搭載了 Google 最新的 `gemini-1.5-flash` 模型，使其具備強大的 AI 對話與工具呼叫能力。

使用者不僅可以透過簡易指令查詢即時的地震報告與預警，還能用自然語言（例如：「幫我找找昨天規模5以上的地震」）與 AI 互動，AI 會自動呼叫外部工具來查詢資料庫，並提供分析後的智慧回答。

## ✨ 主要功能 (Key Features)

* **即時地震報告**: 提供來自 CWA 的最新顯著有感地震報告（含圖）及最近7天的地震列表。
* **全球地震監控**: 整合 USGS 數據，提供全球近24小時及台灣區域的顯著地震資訊。
* **地震預警速報**: 串接 CWA 地震預警 API，提供最新的地震速報。
* **智慧 AI 助理**: 搭載 Google Gemini 1.5 Flash 模型，提供流暢的中文對話能力。
* **AI 工具呼叫 (Tool Calling)**:
    * AI 能夠理解複雜的自然語言問題。
    * 自動呼叫外部的地震資料查詢工具 (MCP-2 Gradio App)。(可用資料 : 1973-01-01 至 2025-07-06)
    * 分析工具回傳的 JSON 資料，並生成人類易於理解的總結性回答。
* **多樣化指令**: 支援 `#` 數字快捷指令，方便使用者快速取用特定功能。

## 🏗️ 專案架構 (Architecture)

本專案採用模組化的 Python Flask 應用程式架構，並透過 Docker 容器化後部署於 Hugging Face Spaces。

1.  **使用者** -> **LINE Platform**
2.  **LINE Platform** -> **Webhook** -> **Hugging Face Space (Gunicorn + Flask)**
3.  `app.py` 接收請求，交由 `command_handler.py` 進行路由。
4.  `command_handler.py` 根據指令類型，分派任務至：
    * `cwa_service.py`: 呼叫台灣中央氣象署 API。
    * `usgs_service.py`: 呼叫美國地質調查局 API。
    * `ai_service.py`: 處理所有 AI 相關邏輯。
5.  **AI 工具呼叫流程**:
    * `ai_service.py` 將使用者問題及工具定義傳送至 **Google Gemini API**。
    * Gemini API 回應，要求呼叫 `call_earthquake_search_tool` 工具。
    * `ai_service.py` 執行該工具，透過 `gradio_client` 呼叫外部的 **MCP-2 Gradio App**。
    * 工具執行結果回傳給 `ai_service.py`。
    * `ai_service.py` 將工具結果再次傳送給 **Gemini API**。
    * Gemini API 根據資料生成最終的自然語言回答。

## 🛠️ 技術棧 (Technology Stack)

* **後端**: Python, Flask, Gunicorn
* **AI 模型**: Google Gemini 1.5 Flash
* **API & 服務**:
    * LINE Messaging API
    * CWA Open Data API
    * USGS Earthquake API
    * Gradio (用於 MCP 工具)
* **部署**: Docker, Hugging Face Spaces

## 部署指南 (Deployment Guide)

本專案已針對 Hugging Face Spaces 部署進行優化，並使用 Secret Variables 安全地管理所有憑證。

### 1. 建立 Hugging Face Space
- 前往 [Hugging Face - New Space](https://huggingface.co/new-space)。
- **Space SDK**: 選擇 **Docker** > **Blank** 模板。
- **Hardware**: 選擇 **CPU basic** (免費方案) 即可。

### 2. 上傳程式碼
- 使用 `git clone` 您的 Space 儲存庫，並將所有專案檔案 (`.py`, `requirements.txt`, `Dockerfile`) 推送上去。

### 3. 設定 Secrets
- 進入您的 Space，點擊 **Settings** > **Secrets**。
- 新增以下 4 個 Secret，名稱必須完全匹配：
  - `CHANNEL_ACCESS_TOKEN`: 您的 LINE Channel Access Token。
  - `CHANNEL_SECRET`: 您的 LINE Channel Secret。
  - `CWA_API_KEY`: 您在氣象署平台申請的 API 金鑰。
  - `GEMINI_API_KEY`: 您從 Google AI Studio 取得的 API 金鑰。

### 4. `Dockerfile`
- 確保您的專案根目錄下有 `Dockerfile` 檔案，內容如下：
  ```dockerfile
  FROM python:3.10-slim
  WORKDIR /code
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 7860
  CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "app:app"]
  ```

### 5. 設定 LINE Webhook
- 複製您的 Space 公開 URL (例如: `https://Your-Username-Your-SpaceName.hf.space`)。
- 在後面加上 `/callback`，組成完整的 Webhook URL。
- 前往 [LINE Developers Console](https://developers.line.biz/console/)，將此 URL 填入您的 Messaging API Channel 的 "Webhook URL" 欄位並啟用。

## 🤖 指令列表 (Command List)

您可以直接輸入指令或對應的 `#` 數字快捷鍵。

```
📖 指令列表 (輸入 #數字 即可)

【地震資訊】
• #1 - 最新一筆顯著地震 (含圖)
• #2 - 全球近24小時顯著地震（USGS)
• #3 - 今年台灣顯著地震列表（USGS)
• #4 - CWA 地震目錄查詢 (外部連結)
• #5 - CWA 最新地震預警
• #6 - CWA 最近7天顯著有感地震

【AI 與工具】
• #7 <問題> - 與 AI 助理對話
  (例如: #7 昨天花蓮有地震嗎？)
  (例如: #7 2024年4月3日規模6以上的地震有哪些？)

【基本指令】
• #8 - 關於此機器人
• #9 - 顯示此說明
```

## 📄 授權 (License)

This project is licensed under the MIT License.


## 技術棧
* **後端**: Python, Flask, Gunicorn
* **LINE 整合**: `line-bot-sdk-python`
* **AI 模型**: Hugging Face `transformers` (`bigscience/bloomz-560m`)
* **部署**: Docker on Hugging Face Spaces
