import requests
import google.generativeai as genai
import os
import json
from datetime import datetime, timedelta, timezone

# APIキーの設定
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Geminiの初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_top_news():
    # 日本(jp)のトップニュースを5件取得
    url = f"https://newsapi.org/v2/top-headlines?country=jp&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get('articles', [])

        if not articles:
            print("Top-headlines returned 0. Switching to everything search...")
            search_url = f"https://newsapi.org/v2/everything?q=ニュース&language=ja&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
            articles = requests.get(search_url).json().get('articles', [])

        return articles
    except Exception as e:
        print(f"NewsAPI Error: {e}")
        return []

def summarize_with_gemini(article):
    content = article.get('description') or article.get('title') or "内容なし"
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大3つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。余計な文章は一切含めないで。
    {{"summary": "...", "glossary": [{{"word": "...", "def": "..."}}]}}

    タイトル: {article['title']}
    内容: {content}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # JSON抽出のガードレール
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except Exception as e:
        print(f"Gemini Error for {article['title']}: {e}")
        return {"summary": "要約の生成に失敗しました。", "glossary": []}

# --- メイン処理 ---
articles = get_top_news()
html_all = ""

if not articles:
    html_all = "<p>現在、取得できるニュースがありません。APIキーの設定を確認してください。</p>"
else:
    for i, art in enumerate(articles):
        ai_data = summarize_with_gemini(art)
        summary = ai_data.get('summary', '要約を生成できませんでした。')
        
        # 専門用語の置換処理
        for g in ai_data.get('glossary', []):
            word = g.get('word')
            definition = g.get('def') or g.get('definition')
            if word and definition:
                summary = summary.replace(word, f'<span class="term" title="{definition}" style="color: #007bff; border-bottom: 2px dotted #007bff; cursor: help; font-weight: bold;">{word}</span>')
        
        html_all += f"""
        <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <span style="background: #eee; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; color: #666;">Top {i+1}</span>
            <h3 style="margin: 10px 0;"><a href="{art['url']}" target="_blank" style="text-decoration: none; color: #1a1a1a;">{art['title']}</a></h3>
            <p style="line-height: 1.7; color: #444; font-size: 1.05em;">{summary}</p>
            <p style="font-size: 0.85em; color: #888; margin-top: 15px; border-top: 1px solid #f9f9f9; padding-top: 10px;">
                📰 {art.get('source', {}).get('name')} | 🕒 {art.get('publishedAt')}
            </p>
        </div>
        """

# 日本時間取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Today's Top 5 News</title>
</head>
<body style="background: #fdfdfd; font-family: -apple-system, sans-serif; padding: 20px; max-width: 800px; margin: auto;">
    <header style="text-align: center; padding: 30px 0;">
        <h1 style="font-size: 2em; margin-bottom: 5px;">🗞️ 日本のトップニュース 5</h1>
        <p style="color: #666;">AIが3文で要約。点線ワードにホバーで用語解説。</p>
        <p style="background: #333; color: #fff; display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em;">{now} 更新</p>
    </header>
    {html_all}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)