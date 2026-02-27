import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta, timezone

# カテゴリID（念のため一番確実な「日本全体」も追加）
TOPIC_IDS = {
    "ニュース全体": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYW1ad0VnSktZWFNoR2dKSlRpZ0Y",
    "ビジネス": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR3QwYjI0U0FpSktZWFNoR2dKSlRpZ0Y",
    "テクノロジー": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR1ptZHpWbUVnSktZWFNoR2dKSlRpZ0Y"
}

html_content = ""

for label, topic_id in TOPIC_IDS.items():
    url = f"https://news.google.com/rss/topics/{topic_id}?hl=ja&gl=JP&ceid=JP:ja"
    print(f"Checking: {label}")
    
    try:
        response = requests.get(url, timeout=15)
        # 通信が成功したかチェック
        if response.status_code != 200:
            html_content += f"<p style='color:red;'>{label}: 通信エラー (Status {response.status_code})</p>"
            continue
            
        root = ET.fromstring(response.text)
        items = root.findall('.//item')
        
        if items:
            title = items[0].find('title').text
            link = items[0].find('link').text
            html_content += f"""
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <b style="color:blue;">[{label}]</b><br>
                <a href="{link}">{title}</a>
            </div>"""
        else:
            html_content += f"<p>{label}: 記事が見つかりませんでした (空のRSS)</p>"
            
    except Exception as e:
        html_content += f"<p style='color:red;'>{label}: 予期せぬエラー ({str(e)})</p>"

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>RSS Test</title></head>
<body>
    <h1>📡 RSS通信テスト画面</h1>
    <p>最終実行: {now}</p>
    {html_content}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)