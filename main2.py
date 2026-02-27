import requests
import xml.etree.ElementTree as ET
import os
import time
from datetime import datetime, timedelta, timezone

# カテゴリ名と検索キーワードの組み合わせ
CATEGORIES = {
    "国内情勢": "日本 政治 国内",
    "世界情勢": "国際 ニュース 世界",
    "ビジネス": "経済 ビジネス 市場",
    "テクノロジー": "IT テクノロジー AI",
    "教育・科学": "教育 科学 研究"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

html_content = ""

for label, query in CATEGORIES.items():
    # 検索方式のURL（安定版）
    url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    
    try:
        # 連続アクセスによるブロックを避けるため少し待機
        time.sleep(1)
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            items = root.findall('.//item')[:3]  # 各カテゴリ最新3件表示
            
            category_html = ""
            for art in items:
                title = art.find('title').text
                link = art.find('link').text
                category_html += f"""
                <li style="margin-bottom: 12px;">
                    <a href="{link}" target="_blank" style="color: #1a0dab; text-decoration: none; font-size: 1.05em;">{title}</a>
                </li>"""
            
            html_content += f"""
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 25px;">
                <h2 style="margin-top: 0; color: #1967d2; border-bottom: 2px solid #e8f0fe; padding-bottom: 10px; font-size: 1.3em;">{label}</h2>
                <ul style="padding-left: 20px; margin-bottom: 0;">
                    {category_html}
                </ul>
            </div>"""
        else:
            html_content += f"<p style='color:red;'>{label}: 取得エラー (Status {response.status_code})</p>"
            
    except Exception as e:
        html_content += f"<p style='color:red;'>{label}: 接続失敗 ({str(e)})</p>"

# 日本時間の取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>最新ニュースまとめ</title>
</head>
<body style="background: #f8f9fa; font-family: -apple-system, sans-serif; padding: 20px; max-width: 800px; margin: auto; color: #333;">
    <header style="text-align: center; margin-bottom: 30px;">
        <h1 style="margin-bottom: 5px;">🗞️ 5カテゴリ最新ニュース</h1>
        <p style="color: #666; font-size: 0.9em;">最終更新（日本時間）: {now}</p>
    </header>
    
    {html_content}
    
    <footer style="text-align: center; margin-top: 40px; color: #999; font-size: 0.8em;">
        Powered by Google News RSS
    </footer>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)