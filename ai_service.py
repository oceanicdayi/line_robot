# ai_service.py (Definitive fix for the ImportError)
import json
from datetime import datetime
import google.generativeai as genai
from gradio_client import Client

# [修正] 移除 'Part' 的 import，因為它導致了錯誤
# from google.generativeai.types import Part

# 從設定檔匯入金鑰和 URL
from config import GEMINI_API_KEY, MCP_SERVER_URL

# --- 1. 設定 Gemini API 金鑰 (一次性設定) ---
if GEMINI_API_KEY and "YOUR_GEMINI_API_KEY" not in GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- 2. 工具函式 (用於地震查詢) ---
def call_mcp_earthquake_search(
    start_date: str,
    end_date: str,
    min_magnitude: float = 4.5,
    max_magnitude: float = 8.0
) -> str:
    """根據指定的條件（時間、規模）從遠端伺服器搜尋地震事件。"""
    try:
        print(f"--- 正在呼叫遠端地震 MCP 伺服器 (由 Gemini 觸發) ---")
        print(f"    查詢條件: {start_date} 到 {end_date}, 規模 {min_magnitude} 以上")

        client = Client(src=MCP_SERVER_URL)
        result = client.predict(
            param_0=start_date, param_1="00:00:00",
            param_2=end_date, param_3="23:59:59",
            param_4=21.0, param_5=26.0, # 預設台灣緯度
            param_6=119.0, param_7=123.0, # 預設台灣經度
            param_8=0.0, param_9=100.0,
            param_10=min_magnitude, param_11=max_magnitude,
            api_name="/gradio_fetch_and_plot_data"
        )
        dataframe_dict = result[0]
        data = dataframe_dict.get('data', [])

        if not data:
            print("--- MCP 伺服器回傳：未找到符合條件的地震 ---")
            return "查詢完成，但未找到任何符合條件的地震資料。"

        headers = dataframe_dict.get('headers', [])
        formatted_results = [dict(zip(headers, row)) for row in data]
        print(f"--- MCP 伺服器成功回傳 {len(data)} 筆資料 ---")
        return json.dumps(formatted_results, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"呼叫 MCP 伺服器失敗: {e}")
        return f"工具執行失敗，錯誤訊息: {e}"

# --- 3. 向 Gemini 定義工具 ---
earthquake_search_tool_declaration = {
    "name": "call_earthquake_search_tool",
    "description": "根據指定的條件（時間、地點、規模等）從台灣中央氣象署的資料庫中搜尋地震事件。預設搜尋台灣周邊地區。",
    "parameters": {
        "type": "OBJECT", "properties": {
            "start_date": {"type": "STRING", "description": "搜尋的開始日期 (格式 'YYYY-MM-DD')。模型應根據使用者問題推斷此日期，例如從『去年』或『2024年』推斷出 '2024-01-01'。"},
            "end_date": {"type": "STRING", "description": "搜尋的結束日期 (格式 'YYYY-MM-DD')。模型應根據使用者問題推斷此日期，例如從『昨天』或『2024年』推斷出 '2024-12-31'。"},
            "min_magnitude": {"type": "NUMBER", "description": "要搜尋的最小地震規模。如果使用者未指定，請使用預設值 4.5。"},
            "max_magnitude": {"type": "NUMBER", "description": "要搜尋的最大地震規模。預設為 8.0。"},
        }, "required": ["start_date", "end_date"]
    }
}

available_tools = {"call_earthquake_search_tool": call_mcp_earthquake_search}

# --- 4. 建立 Gemini 模型 ---
model = None
if GEMINI_API_KEY and "YOUR_GEMINI_API_KEY" not in GEMINI_API_KEY:
    try:
        system_instruction = (
            "You are a helpful AI assistant. You must answer in Traditional Chinese."
            "You have access to tools. When a tool returns data in JSON format, "
            "you must analyze the JSON data to fully answer the user's question. "
            "For example, if the user asks for the largest earthquake, use the search tool for the relevant date range "
            "and then find the entry with the highest magnitude from the JSON results before answering."
        )
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[earthquake_search_tool_declaration],
            system_instruction=system_instruction
        )
    except Exception as e:
        print(f"建立 Gemini 模型失敗: {e}")

# --- 5. 主要的 AI 文字生成函式 ---
def generate_ai_text(user_prompt: str) -> str:
    if not model:
        return "🤖 AI (Gemini) 服務尚未設定 API 金鑰，或金鑰無效。"
    try:
        print(f"--- 開始 Gemini 對話，使用者輸入: '{user_prompt}' ---")
        chat = model.start_chat()
        response = chat.send_message(user_prompt)
        try:
            function_call = response.candidates[0].content.parts[0].function_call
        except (IndexError, AttributeError):
            function_call = None
        if not function_call:
            print("--- Gemini 直接回覆文字 ---")
            return response.text
        
        print(f"--- Gemini 要求呼叫工具: {function_call.name} ---")
        tool_function = available_tools.get(function_call.name)
        if not tool_function:
            return f"錯誤：模型嘗試呼叫一個不存在的工具 '{function_call.name}'。"
        
        tool_result = tool_function(**dict(function_call.args))
        print("--- 將工具結果回傳給 Gemini ---")
        
        # [修正] 直接傳送包含 function_response 的字典，不再使用 Part 類別
        response = chat.send_message(
            {"function_response": {"name": function_call.name, "response": {"result": tool_result}}}
        )
        
        print("--- Gemini 根據工具結果生成最終回覆 ---")
        return response.text
    except Exception as e:
        print(f"與 Gemini AI 互動時發生錯誤: {e}")
        return f"🤖 AI 服務發生錯誤: {e}"

