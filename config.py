# config.py (Gemini 最終版)
import os
import tempfile
from datetime import datetime

# ==============================================================================
# 1. 執行環境設定 (適用於 Hugging Face Spaces)
# ==============================================================================

# 設定一個暫存目錄給 Matplotlib 快取字體 (若未來有繪圖功能)
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

# 定義一個暫存目錄來存放生成的靜態檔案
STATIC_DIR = os.getenv("STATIC_DIR", os.path.join(tempfile.gettempdir(), "static"))
os.makedirs(STATIC_DIR, exist_ok=True)


# ==============================================================================
# 2. 憑證與金鑰 (從 Secret Variables 讀取)
# ==============================================================================

# LINE Bot 憑證
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

# CWA (中央氣象署) API 金鑰
CWA_API_KEY = os.getenv("CWA_API_KEY")

# Google Gemini API 金鑰
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ==============================================================================
# 3. API 端點與 URL
# ==============================================================================

# CWA API 端點
CWA_ALARM_API = "https://app-2.cwa.gov.tw/api/v1/earthquake/alarm/list"
CWA_SIGNIFICANT_API = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001"

# USGS API 端點
USGS_API_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# MCP 伺服器 (Gradio App) URL
MCP_SERVER_URL = "https://cwadayi-mcp-2.hf.space"


# ==============================================================================
# 4. 一般應用程式設定
# ==============================================================================

# 顯示用的當年年份
CURRENT_YEAR = datetime.now().year

