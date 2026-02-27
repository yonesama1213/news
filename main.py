import requests
import google.generativeai as genai
import os
import json
from datetime import datetime, timedelta, timezone # これを追加！

# 設定（GitHub ActionsのSecretsから読み込む）
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_news(category):
    url = f"https://newsapi.org/v2/top-headlines?country=jp&category={category}&pageSize=2&apiKey={NEWS_API_KEY}"
    return requests.get(url).json().get('articles', [])

def summarize_article(article):
    prompt = f"以下のニュースを3文で要約し、専門用語を最大3つ抽出して解説してください。必ずJSON形式 {{'summary': '...', 'glossary': [{{'word': '...', 'def': '...'}}]}} で返して。タイトル: {article['title']} 内容: {article.get('description', '')}"
    try:
        response = model.generate_content(prompt)
        # Geminiの返答からJSON部分だけを抽出
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {"summary": "要約に失敗しました。", "glossary": []}

# ニュース取得と要約
categories = {"general": "国内・世界", "technology": "テクノロジー", "business": "ビジネス", "science": "教育・科学"}
html_content = ""

for cat_id, cat_name in categories.items():
    articles = get_news(cat_id)
    html_content += f"<h2>{cat_name}</h2>"
    for art in articles:
        data = summarize_article(art)
        summary = data['summary']
        # 専門用語にポップアップを仕込む
        for g in data['glossary']:
            summary = summary.replace(g['word'], f'<span class="term" title="{g["def"]}">{g["word"]}</span>')
        
        html_content += f"""
        <div class="card">
            <h3><a href="{art['url']}">{art['title']}</a></h3>
            <p>{summary}</p>
        </div>"""

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

# index.htmlを作成
template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>マイニュース要約</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #f0f2f5; }}
        .card {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .term {{ color: #007bff; border-bottom: 1px dotted #007bff; cursor: help; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>📰 最新ニュース要約</h1>
    {html_content}
    <p style="font-size: 0.8em;">最終更新（日本時間）: {now}</p>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)