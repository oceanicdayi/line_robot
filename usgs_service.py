# usgs_service.py
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from config import USGS_API_BASE_URL, CURRENT_YEAR

def _iso(dt: datetime) -> str:
    """將 datetime 物件格式化為 USGS API 需要的 ISO 8601 字串。"""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

def fetch_global_last24h_text(min_mag: float = 5.0, limit: int = 10) -> str:
    """從 USGS 擷取過去 24 小時的全球顯著地震。"""
    now_utc = datetime.now(timezone.utc)
    since = now_utc - timedelta(hours=24)
    params = {
        "format": "geojson",
        "starttime": _iso(since),
        "endtime": _iso(now_utc),
        "minmagnitude": float(min_mag),
        "limit": int(limit),
        "orderby": "time",
    }
    try:
        r = requests.get(USGS_API_BASE_URL, params=params, timeout=15)
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            return f"✅ 過去 24 小時內，全球無規模 {min_mag} 以上的顯著地震。"
        
        lines = [f"🚨 近 24 小時全球顯著地震 (M≥{min_mag}):", "-" * 20]
        for f in features:
            p = f["properties"]
            t_utc = datetime.fromtimestamp(p["time"] / 1000, tz=timezone.utc)
            
            lines.append(
                # [修改] 將 "震級" 改為 "規模"
                f"規模: {p['mag']:.1f} | 日期時間: {t_utc.strftime('%Y-%m-%d %H:%M')} (UTC)\n"
                f"地點: {p.get('place', 'N/A')}\n"
                f"報告連結: {p.get('url', '無')}"
            )
        return "\n\n".join(lines)
    except Exception as e:
        return f"❌ 查詢失敗：{e}"

def fetch_taiwan_df_this_year(min_mag: float = 5.0) -> pd.DataFrame | str:
    """從USGS擷取今年以來台灣區域的顯著地震。"""
    now_utc = datetime.now(timezone.utc)
    start_of_year_utc = datetime(now_utc.year, 1, 1, tzinfo=timezone.utc)
    params = {
        "format": "geojson", "starttime": _iso(start_of_year_utc), "endtime": _iso(now_utc),
        "minmagnitude": float(min_mag),
        "minlatitude": 21, "maxlatitude": 26,
        "minlongitude": 119, "maxlongitude": 123,
        "limit": 250,
        "orderby": "time",
    }
    try:
        r = requests.get(USGS_API_BASE_URL, params=params, timeout=20)
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            return f"✅ 今年 ({CURRENT_YEAR} 年) 以來，台灣區域無 M≥{min_mag:.1f} 的顯著地震。"
        
        rows = []
        for f in features:
            p = f["properties"]
            lon, lat, *_ = f["geometry"]["coordinates"]
            rows.append({
                "latitude": lat, 
                "longitude": lon, 
                "magnitude": p["mag"],
                "place": p.get("place", ""), 
                "time_utc": datetime.fromtimestamp(p["time"]/1000, tz=timezone.utc),
                "url": p.get("url", "")
            })
        return pd.DataFrame(rows)
    except Exception as e:
        return f"❌ 查詢失敗: {e}"
