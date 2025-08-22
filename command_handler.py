# command_handler.py (Corrected and Modified Version)
import pandas as pd
from linebot.v3.messaging import TextMessage, ImageMessage

# 匯入所有服務函式
from cwa_service import fetch_cwa_alarm_list, fetch_significant_earthquakes, fetch_latest_significant_earthquake
from usgs_service import fetch_global_last24h_text, fetch_taiwan_df_this_year
from plotting_service import create_and_save_map
from ai_service import generate_ai_text
# [修正] 將 HF_SPACE_URL 改為 MCP_SERVER_URL
from config import CURRENT_YEAR, MCP_SERVER_URL

def get_help_message() -> TextMessage:
    text = (
        "📖 指令列表 (輸入數字即可)\n\n"
        "【地震資訊】\n"
        "• 1 - 最新一筆顯著地震 (含圖)\n"
        "• 2 - 全球近24小時顯著地震（USGS)\n"
        "• 3 - 今年台灣顯著地震列表（USGS)\n"
        "• 4 - CWA 地震目錄查詢 (外部連結)\n"
        "• 5 - CWA 最新地震預警\n"
        "• 6 - CWA 最近7天顯著有感地震\n\n"
        "【AI 與工具】\n"
        "• 7 <問題> - 與 AI 助理對話\n\n"
        "【基本指令】\n"
        "• 8 - 關於此機器人\n"
        "• 9 - 顯示此說明"
    )
    return TextMessage(text=text)

def get_info_message() -> TextMessage:
    text = (
        "🤖 關於我\n\n"
        "我是一個多功能助理機器人，提供地震查詢與 AI 對話功能。\n\n"
        "• 版本: 5.0 (Gemini Edition) 搭配搜尋地震目錄的MCP功能（可用資料 : 1973-01-01 至 2025-07-06）\n"
        "• 資料來源: CWA, USGS, Google Gemini\n"
        "• 開發者: dayichen"
    )
    return TextMessage(text=text)

def get_taiwan_earthquake_list() -> TextMessage:
    result = fetch_taiwan_df_this_year()
    if isinstance(result, pd.DataFrame):
        count = len(result)
        lines = [f"🇹🇼 今年 ({CURRENT_YEAR} 年) 台灣區域顯著地震 (M≥5.0)，共 {count} 筆:", "-" * 20]
        for _, row in result.head(15).iterrows():
            t = row["time_utc"].strftime("%Y-%m-%d %H:%M")
            lines.append(
                f"規模: {row['magnitude']:.1f} | 日期時間: {t} (UTC)\n"
                f"地點: {row['place']}\n"
                f"報告連結: {row.get('url', '無')}"
            )
        if count > 15:
            lines.append(f"... (還有 {count-15} 筆資料)")
        reply_text = "\n\n".join(lines)
    else:
        reply_text = result
    return TextMessage(text=reply_text)

def get_latest_earthquake_reply() -> list:
    try:
        latest_eq = fetch_latest_significant_earthquake()
        if not latest_eq:
            return [TextMessage(text="✅ 近期無顯著有感地震報告。")]

        mag_str = f"{latest_eq['Magnitude']:.1f}" if latest_eq.get('Magnitude') is not None else "—"
        depth_str = f"{latest_eq['Depth']:.0f}" if latest_eq.get('Depth') is not None else "—"
        
        text_message_content = (
            f"🚨 CWA 最新顯著有感地震\n"
            f"----------------------------------\n"
            f"時間: {latest_eq.get('TimeStr', '—')}\n"
            f"地點: {latest_eq.get('Location', '—')}\n"
            f"規模: M{mag_str} | 深度: {depth_str} km\n"
            f"報告: {latest_eq.get('URL', '無')}"
        )
        reply_messages = [TextMessage(text=text_message_content)]

        if latest_eq.get("ImageURL"):
            image_url = latest_eq["ImageURL"]
            reply_messages.append(
                ImageMessage(original_content_url=image_url, preview_image_url=image_url)
            )
        
        return reply_messages
    except Exception as e:
        return [TextMessage(text=f"❌ 查詢最新地震失敗：{e}")]

def process_message(user_message_raw: str, request_base_url: str) -> list:
    user_message = (user_message_raw or "").strip()
    
    cmd_map = {
        '1': '/latest', '2': '/global', '3': '/taiwan',
        '4': '/map', '5': '/alert', '6': '/significant',
        '7': '/ai', '8': '/info', '9': '/help',
        '地震': '/global', 'quake': '/global', '幫助': '/help',
        '台灣地震': '/taiwan', '臺灣地震': '/taiwan',
        '台灣地震畫圖': '/map', '臺灣地震畫圖': '/map',
        '地震預警': '/alert',
    }

    command = ""
    arg = ""
    
    parts = user_message.split(' ', 1)
    cmd_key = parts[0].lower()

    if cmd_key in cmd_map:
        command = cmd_map[cmd_key]
        if len(parts) > 1:
            arg = parts[1].strip()
    # Allow users to still use /command format
    elif user_message.startswith('/') and cmd_key in cmd_map.values():
        command = cmd_key
        if len(parts) > 1:
            arg = parts[1].strip()

    if command:
        if command == '/help': return [get_help_message()]
        if command == '/info': return [get_info_message()]
        if command == '/latest': return get_latest_earthquake_reply()
        if command == '/global': return [TextMessage(text=fetch_global_last24h_text())]
        if command == '/taiwan': return [get_taiwan_earthquake_list()]
        # [修正] 將 HF_SPACE_URL 改為 MCP_SERVER_URL
        if command == '/map': return [TextMessage(text=f"🗺️ 外部地震查詢服務\n\n請點擊以下連結：\n{MCP_SERVER_URL}")]
        if command == '/alert': return [TextMessage(text=fetch_cwa_alarm_list(limit=5))]
        if command == '/significant': return [TextMessage(text=fetch_significant_earthquakes(limit=5))]
        if command == '/ai':
            prompt = arg
            if not prompt: return [TextMessage(text="請輸入問題，例如：7 台灣最高的山是哪座？")]
            return [TextMessage(text=generate_ai_text(prompt))]

    return [TextMessage(text=generate_ai_text(user_message))]
