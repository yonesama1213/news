import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import json
from datetime import datetime, timedelta, timezone

# APIキーの設定（Geminiのみ必須）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_google_news():
    # 日本のトップニュースRSS
    url = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
    response = requests.get(url)
    root = ET.fromstring(response.text)
    articles = []
    # 確実にニュースを出すため、最新の5〜8件程度を対象にする
    for item in root.findall('.//item')[:6]:
        articles.append({
            'title': item.find('title').text,
            'link': item.find('link').text
        })
    return articles

def summarize_with_gemini(title):
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大3つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。余計な文章は一切含めないで。
    {{"summary": "...", "glossary": [{{"word": "...", "def": "..."}}]}}
    タイトル: {title}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        return {"summary": "要約の生成に失敗しました。", "glossary": []}

# --- 実行 ---
articles = get_google_news()
html_cards = ""

for i, art in enumerate(articles):
    ai_data = summarize_with_gemini(art['title'])
    summary = ai_data.get('summary', '要約不可')
    
    # 専門用語をポップアップ化
    for g in ai_data.get('glossary', []):
        word = g.get('word')
        definition = g.get('def')
        if word and definition:
            summary = summary.replace(word, f'<span class="term" title="{definition}">{word}</span>')
    
    html_cards += f"""
    <div class="card">
        <small>Top {i+1}</small>
        <h3><a href="{art['link']}" target="_blank">{art['title']}</a></h3>
        <p>{summary}</p>
    </div>
    """

# 日本時間
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

# HTMLテンプレート
template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIニュース要約</title>
    <style>
        body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; max-width: 800px; margin: auto; color: #333; }}
        h1 {{ text-align: center; color: #2c3e50; }}
        .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .card h3 {{ margin: 10px 0; font-size: 1.2em; }}
        .card a {{ color: #007bff; text-decoration: none; }}
        .term {{ color: #e74c3c; border-bottom: 2px dotted #e74c3c; cursor: help; font-weight: bold; }}
        .update-time {{ text-align: center; font-size: 0.8em; color: #95a5a6; }}
    </style>
</head>
<body>
    <h1>📰 AIニュース要約くん</h1>
    <p class="update-time">最終更新: {now}</p>
    {html_cards}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)