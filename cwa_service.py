# cwa_service.py (Final Defensive Parsing Version)
import requests
import re
import pandas as pd
from datetime import datetime, timedelta, timezone
from config import CWA_API_KEY, CWA_ALARM_API, CWA_SIGNIFICANT_API

TAIPEI_TZ = timezone(timedelta(hours=8))

def _to_float(x):
    if x is None: return None
    s = str(x).strip()
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None

def _parse_cwa_time(s: str) -> tuple[str, str]:
    if not s: return ("未知", "未知")
    dt_utc = None
    try:
        dt_utc = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt_local = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            dt_local = dt_local.replace(tzinfo=TAIPEI_TZ)
            dt_utc = dt_local.astimezone(timezone.utc)
        except Exception:
            return (s, "未知")
    if dt_utc:
        tw_str = dt_utc.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M")
        utc_str = dt_utc.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        return (tw_str, utc_str)
    return (s, "未知")

def fetch_cwa_alarm_list(limit: int = 5) -> str:
    try:
        r = requests.get(CWA_ALARM_API, timeout=10)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        return f"❌ 地震預警查詢失敗：{e}"
    items = payload.get("data", [])
    if not items: return "✅ 目前沒有地震預警。"
    def _key(it):
        try: return datetime.fromisoformat(it.get("originTime", "").replace("Z", "+00:00"))
        except: return datetime.min.replace(tzinfo=timezone.utc)
    items = sorted(items, key=_key, reverse=True)
    lines = ["🚨 地震預警（最新）:", "-" * 20]
    for it in items[:limit]:
        mag = _to_float(it.get("magnitudeValue"))
        depth = _to_float(it.get("depth"))
        tw_str, _ = _parse_cwa_time(it.get("originTime", ""))
        identifier = str(it.get('identifier', '—')).replace('{', '{{').replace('}', '}}')
        msg_type = str(it.get('msgType', '—')).replace('{', '{{').replace('}', '}}')
        msg_no = str(it.get('msgNo', '—')).replace('{', '{{').replace('}', '}}')
        location_desc_list = it.get('locationDesc')
        areas_str = ", ".join(str(area) for area in location_desc_list) if isinstance(location_desc_list, list) and location_desc_list else "—"
        areas = areas_str.replace('{', '{{').replace('}', '}}')
        mag_str = f"{mag:.1f}" if mag is not None else "—"
        depth_str = f"{depth:.0f}" if depth is not None else "—"
        lines.append(
            f"事件: {identifier} | 類型: {msg_type}#{msg_no}\n"
            f"規模/深度: M{mag_str} / {depth_str} km\n"
            f"時間: {tw_str}（台灣）\n"
            f"地點: {areas}"
        )
    return "\n\n".join(lines).strip()

def _parse_significant_earthquakes(obj: dict) -> pd.DataFrame:
    records = obj.get("records", {})
    quakes = records.get("Earthquake", [])
    rows = []
    for q in quakes:
        # [偵錯] 如果需要，可以取消下面這行的註解，它會在 Log 中印出最原始的資料
        # print(f"原始地震資料: {q}") 
        
        ei = q.get("EarthquakeInfo", {})
        
        # [修正] 使用更穩健的方式取得所有資料，檢查所有已知的大小寫和備用名稱
        epic = ei.get("Epicenter") or ei.get("epicenter") or {}
        mag_info = ei.get("Magnitude") or ei.get("magnitude") or ei.get("EarthquakeMagnitude") or {}
        depth_raw = ei.get("FocalDepth") or ei.get("depth") or ei.get("Depth")
        mag_raw = mag_info.get("MagnitudeValue") or mag_info.get("magnitudeValue") or mag_info.get("Value") or mag_info.get("value")
        
        rows.append({
            "ID": q.get("EarthquakeNo"), "Time": ei.get("OriginTime"),
            "Lat": _to_float(epic.get("EpicenterLatitude") or epic.get("epicenterLatitude")),
            "Lon": _to_float(epic.get("EpicenterLongitude") or epic.get("epicenterLongitude")),
            "Depth": _to_float(depth_raw), 
            "Magnitude": _to_float(mag_raw),
            "Location": epic.get("Location") or epic.get("location"), 
            "URL": q.get("Web") or q.get("ReportURL"),
        })
        
    df = pd.DataFrame(rows)
    if not df.empty and "Time" in df.columns:
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce", utc=True).dt.tz_convert(TAIPEI_TZ)
    return df

def fetch_significant_earthquakes(days: int = 7, limit: int = 5) -> str:
    if not CWA_API_KEY: return "❌ 顯著地震查詢失敗：管理者尚未設定 CWA_API_KEY。"
    now = datetime.now(timezone.utc)
    time_from = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {"Authorization": CWA_API_KEY, "format": "JSON", "timeFrom": time_from}
    try:
        r = requests.get(CWA_SIGNIFICANT_API, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        df = _parse_significant_earthquakes(data)
        if df.empty: return f"✅ 過去 {days} 天內沒有顯著有感地震報告。"
        df = df.sort_values(by="Time", ascending=False).head(limit)
        lines = [f"🚨 CWA 最新顯著有感地震 (近{days}天内):", "-" * 20]
        for _, row in df.iterrows():
            mag_str = f"{row['Magnitude']:.1f}" if pd.notna(row['Magnitude']) else "—"
            depth_str = f"{row['Depth']:.0f}" if pd.notna(row['Depth']) else "—"
            lines.append(
                f"時間: {row['Time'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['Time']) else '—'}\n"
                f"地點: {row['Location'] or '—'}\n"
                f"規模: M{mag_str} | 深度: {depth_str} km\n"
                f"報告: {row['URL'] or '無'}"
            )
        return "\n\n".join(lines)
    except Exception as e:
        return f"❌ 顯著地震查詢失敗：{e}"

def fetch_latest_significant_earthquake() -> dict | None:
    try:
        if not CWA_API_KEY: raise ValueError("錯誤：尚未設定 CWA_API_KEY Secret。")
        params = {"Authorization": CWA_API_KEY, "format": "JSON", "limit": 1, "orderby": "OriginTime desc"}
        r = requests.get(CWA_SIGNIFICANT_API, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        df = _parse_significant_earthquakes(data)
        if df.empty: return None

        latest_eq_data = df.iloc[0].to_dict()
        
        quakes = data.get("records", {}).get("Earthquake", [])
        if quakes:
            latest_eq_data["ImageURL"] = quakes[0].get("ReportImageURI")

        if pd.notna(latest_eq_data.get("Time")):
            latest_eq_data["TimeStr"] = latest_eq_data["Time"].strftime('%Y-%m-%d %H:%M')

        return latest_eq_data
    except Exception as e:
        raise e

