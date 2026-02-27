import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import json
import time
from datetime import datetime, timedelta, timezone

# APIキーの設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# GoogleニュースのカテゴリID (RSS用)
TOPIC_IDS = {
    "国内情勢": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYW1ad0VnSktZWFNoR2dKSlRpZ0Y",
    "世界情勢": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRmx1Y3pnd0VnSktZWFNoR2dKSlRpZ0Y",
    "ビジネス": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR3QwYjI0U0FpSktZWFNoR2dKSlRpZ0Y",
    "テクノロジー": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR1ptZHpWbUVnSktZWFNoR2dKSlRpZ0Y",
    "教育・科学": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR1p0Y25Oc0VnSktZWFNoR2dKSlRpZ0Y"
}

def get_category_news(topic_id):
    url = f"https://news.google.com/rss/topics/{topic_id}?hl=ja&gl=JP&ceid=JP:ja"
    try:
        response = requests.get(url, timeout=15)
        root = ET.fromstring(response.text)
        item = root.find('.//item')
        if item is not None:
            return {'title': item.find('title').text, 'link': item.find('link').text}
    except Exception as e:
        print(f"RSS取得エラー: {e}")
    return None

def summarize_with_gemini(title):
    prompt = f"""
    以下のニュースタイトルから内容を推測し、3文で要約してください。
    また、文中の専門用語を最大3つ抽出し解説してください。
    出力は必ず以下のJSON形式のみとしてください。
    {{ "summary": "...", "glossary": [{{ "word": "...", "def": "..." }}] }}
    タイトル: {title}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # JSON部分を確実に抽出するロジック
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            return {"summary": f"JSON解析エラー: {text[:50]}...", "glossary": []}
        return json.loads(text[start:end])
    except Exception as e:
        return {"summary": f"Geminiエラー: {str(e)}", "glossary": []}

# --- 実行 ---
html_content = ""
for label, topic_id in TOPIC_IDS.items():
    article = get_category_news(topic_id)
    if article:
        ai_data = summarize_with_gemini(article['title'])
        summary = ai_data.get('summary', '要約なし')
        for g in ai_data.get('glossary', []):
            word, definition = g.get('word'), g.get('def')
            if word and definition:
                summary = summary.replace(word, f'<span class="term" title="{definition}">{word}</span>')
        
        html_content += f"""
        <div class="card">
            <div class="category-label">{label}</div>
            <h3><a href="{article['link']}" target="_blank">{article['title']}</a></h3>
            <p>{summary}</p>
        </div>
        """
        time.sleep(1) # API制限対策

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

# HTMLテンプレート (閉じ忘れのないように慎重に！)
template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIニュース要約</title>
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; max-width: 800px; margin: auto; }}
        .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .category-label {{ background: #e8f0fe; color: #1967d2; font-size: 0.8em; padding: 4px 10px; border-radius: 10px; }}
        .term {{ color: #d93025; border-bottom: 2px dotted #d93025; cursor: help; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>📰 AIニュース要約</h1>
    <p>最終更新: {now}</p>
    {html_content}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)