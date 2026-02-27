import requests
import xml.etree.ElementTree as ET
import os
import time
from datetime import datetime, timedelta, timezone

# URLを検索方式に変更（これなら400エラーが出にくいです）
# 「q=ニュース」というキーワードで最新を検索
url = "https://news.google.com/rss/search?q=国内情勢&hl=ja&gl=JP&ceid=JP%3Aja"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

html_content = ""

try:
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        items = root.findall('.//item')[:5]  # 最新5件
        
        for art in items:
            title = art.find('title').text
            link = art.find('link').text
            html_content += f"""
            <div style="background:white; padding:15px; border-radius:8px; margin-bottom:10px; border-left:5px solid #007bff; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <a href="{link}" target="_blank" style="text-decoration:none; color:#1a0dab; font-weight:bold;">{title}</a>
            </div>"""
    else:
        html_content = f"<p style='color:red;'>エラー発生 (Status {response.status_code})<br>このURLをブラウザで開けるか試してください: <a href='{url}'>{url}</a></p>"

except Exception as e:
    html_content = f"<p style='color:red;'>接続失敗: {str(e)}</p>"

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>RSS Search Test</title></head>
<body style="background:#f0f2f5; font-family:sans-serif; padding:20px; max-width:600px; margin:auto;">
    <h1>🗞️ ニュース取得テスト（検索方式）</h1>
    <p>最終実行: {now}</p>
    {html_content}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)