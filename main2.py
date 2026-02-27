import requests
import xml.etree.ElementTree as ET
import os
import time
from datetime import datetime, timedelta, timezone

# カテゴリID（URLを生成するためのパラメータ）
TOPIC_IDS = {
    "ニュース全体": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYW1ad0VnSktZWFNoR2dKSlRpZ0Y",
    "ビジネス": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR3QwYjI0U0FpSktZWFNoR2dKSlRpZ0Y",
    "テクノロジー": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR1ptZHpWbUVnSktZWFNoR2dKSlRpZ0Y"
}

html_content = ""

# ブラウザからのアクセスに見せかけるためのヘッダー
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

for label, topic_id in TOPIC_IDS.items():
    # URLをよりシンプルな形式に変更
    url = f"https://news.google.com/rss/topics/{topic_id}?hl=ja&gl=JP&ceid=JP%3Aja"
    
    try:
        # 1秒待機して連続アクセスを避ける（400エラー対策）
        time.sleep(1)
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            items = root.findall('.//item')
            if items:
                title = items[0].find('title').text
                link = items[0].find('link').text
                html_content += f"""
                <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px; background: white;">
                    <b style="color:blue;">[{label}]</b><br>
                    <a href="{link}" target="_blank">{title}</a>
                </div>"""
        else:
            # エラーが出た場合、URLとステータスを表示
            html_content += f"<p style='color:red;'>{label}: エラー (Status {response.status_code})<br><small>URL: {url}</small></p>"
            
    except Exception as e:
        html_content += f"<p style='color:red;'>{label}: 接続失敗 ({str(e)})</p>"

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>RSS Debug</title></head>
<body style="background:#f9f9f9; font-family:sans-serif; padding:20px;">
    <h1>📡 400エラー対策・通信テスト</h1>
    <p>最終実行: {now}</p>
    {html_content}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)