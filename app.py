# app.py
# 首先匯入 config，以設定環境變數
import config

from flask import Flask, request, abort, send_from_directory
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 匯入指令處理器
from command_handler import process_message

# ------------------------------------------------------------------------------
# Flask & LINE Bot 設定
# ------------------------------------------------------------------------------
app = Flask(__name__)
line_config = Configuration(access_token=config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)

# ------------------------------------------------------------------------------
# Web 伺服器路由
# ------------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    """[修改] 渲染一個簡潔的機器人狀態首頁。"""
    return """
<!doctype html>
<html lang="zh-Hant">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LINE Bot Server Status</title>
    <style>
        body {
            background-color: #0f1115;
            color: #e6e8ef;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            text-align: center;
        }
        .container {
            padding: 2rem;
        }
        h1 {
            font-size: 2.2rem;
            margin-bottom: 1rem;
            color: #ffffff;
        }
        .status-ok {
            color: #22c55e; /* Green */
        }
        p {
            font-size: 1.1rem;
            color: #9aa4b2;
            line-height: 1.6;
            max-width: 600px;
        }
        .active {
            font-weight: bold;
            color: #22c55e; /* Green */
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><span class="status-ok">✓</span> LINE Bot Server is Running</h1>
        <p>This is the backend service for the Earthquake Alert Bot.</p>
        <p>The service is <span class="active">active</span> and listening for webhook events from LINE.</p>
    </div>
</body>
</html>
"""

@app.route("/healthz")
def healthz():
    """健康檢查端點。"""
    return "ok"

@app.route("/static/<path:filename>")
def serve_static(filename):
    """提供靜態檔案（例如，生成的地圖）。"""
    return send_from_directory(config.STATIC_DIR, filename)

# ------------------------------------------------------------------------------
# LINE Webhook 處理器
# ------------------------------------------------------------------------------
@app.route("/callback", methods=["POST"])
def callback():
    """處理來自 LINE 平台的傳入 Webhooks。"""
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """
    處理來自使用者的文字訊息並回覆。
    所有邏輯都委派給 command_handler。
    """
    base_url = request.url_root.rstrip("/")
    reply_messages = process_message(event.message.text, base_url)
    
    with ApiClient(line_config) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=reply_messages
            )
        )
