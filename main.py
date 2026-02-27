import requests
import os
from datetime import datetime, timedelta, timezone

# 設定（NewsAPIキーのみ使用）
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_news(category):
    # 日本のニュースを取得
    url = f"https://newsapi.org/v2/top-headlines?country=jp&category={category}&pageSize=5&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    # APIのレスポンスが正しいかチェック
    if data.get("status") != "ok":
        print(f"API Error in {category}: {data.get('message')}")
        return []
        
    return data.get('articles', [])

# ニュース取得
categories = {"general": "国内・世界", "technology": "テクノロジー", "business": "ビジネス", "science": "教育・科学"}
html_content = ""

for cat_id, cat_name in categories.items():
    articles = get_news(cat_id)
    html_content += f"<h2>{cat_name} ({len(articles)}件ヒット)</h2>"
    
    if not articles:
        html_content += "<p>この記事カテゴリは現在空です。</p>"
    
    for art in articles:
        # タイトルとリンクだけのシンプルな表示
        html_content += f"""
        <div class="card" style="background: white; padding: 10px; margin-bottom: 5px; border-radius: 5px;">
            <h3><a href="{art['url']}" target="_blank">{art['title']}</a></h3>
            <p>ソース: {art.get('source', {}).get('name', '不明')}</p>
        </div>"""

# 日本時間を取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

# index.htmlを作成
template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NewsAPI テスト表示</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #f0f2f5; }}
        h2 {{ border-left: 5px solid #007bff; padding-left: 10px; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>🧪 NewsAPI 取得テスト</h1>
    <p>最終実行: {now}</p>
    {html_content}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)