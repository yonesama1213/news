import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import json
from datetime import datetime, timedelta, timezone

# Geminiの設定のみ使用
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_google_news():
    # GoogleニュースのRSSから日本の最新ニュースを取得
    url = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
    response = requests.get(url)
    root = ET.fromstring(response.text)
    articles = []
    # 最新の5件を抽出
    for item in root.findall('.//item')[:5]:
        articles.append({
            'title': item.find('title').text,
            'link': item.find('link').text
        })
    return articles

def summarize_with_gemini(title):
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大3つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。
    {{"summary": "...", "glossary": [{{"word": "...", "def": "..."}}]}}
    タイトル: {title}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        start, end = text.find('{'), text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        return {"summary": "要約に失敗しました。", "glossary": []}

# --- メイン処理 ---
articles = get_google_news()
html_all = ""

for art in articles:
    ai_data = summarize_with_gemini(art['title'])
    summary = ai_data['summary']
    for g in ai_data['glossary']:
        summary = summary.replace(g['word'], f'<span title="{g["def"]}" style="color:blue;cursor:help;border-bottom:1px dotted;">{g["word"]}</span>')
    
    html_all += f"<div><h3><a href='{art['link']}'>{art['title']}</a></h3><p>{summary}</p></div>"

# HTML書き出し（デザインは簡略化）
with open("index.html", "w", encoding="utf-8") as f:
    f.write(f"<html><body><h1>🗞️ AIニュース要約</h1>{html_all}</body></html>")