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

def get_news(query):
    # 日本語の最新ニュースを確実に拾うためのURL
    url = f"https://newsapi.org/v2/everything?q={query}&language=ja&pageSize=2&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        return response.json().get('articles', [])
    except Exception as e:
        print(f"NewsAPI Error ({query}): {e}")
        return []

def summarize_with_gemini(article):
    # 記事の中身が薄い場合でも要約させるための工夫
    content = article.get('description') or article.get('title') or "内容なし"
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大3つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。余計な文章は一切含めないで。
    {{"summary": "要約文1。要約文2。要約文3。", "glossary": [{{"word": "単語", "def": "解説"}}]}}

    タイトル: {article['title']}
    内容: {content}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # ログにGeminiの生の結果を出す（不具合確認用）
        print(f"--- Gemini Response for '{article['title'][:20]}...' ---")
        print(text)
        
        # JSON部分を無理やり抽出（```json などの付着対策）
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("JSONが見つかりません")
            
        return json.loads(text[start:end])
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"summary": f"要約の処理中にエラーが発生しました。({e})", "glossary": []}

# --- メイン処理：5つのカテゴリを指定 ---
# 検索ワードを工夫して、ニュースがヒットしやすくしています
categories = {
    "日本 政治 国内": "国内情勢",
    "世界 情勢 国際ニュース": "世界情勢",
    "最新 IT テクノロジー AI": "テクノロジー",
    "日本 経済 ビジネス": "ビジネス",
    "教育 学校 学習": "教育"
}

html_all = ""

for query, label in categories.items():
    articles = get_news(query)
    html_all += f"<h2 style='border-bottom: 2px solid #333; margin-top: 40px;'>{label}</h2>"
    
    if not articles:
        html_all += "<p>このカテゴリのニュースは見つかりませんでした。</p>"
        continue

    # 各カテゴリから1つのトップニュースを処理
    art = articles[0]
    ai_data = summarize_with_gemini(art)
    
    summary = ai_data.get('summary', '要約なし')
    # 専門用語の置換処理
    for g in ai_data.get('glossary', []):
        word = g.get('word')
        definition = g.get('def')
        if word and definition:
            summary = summary.replace(word, f'<span class="term" title="{definition}" style="color: #d9534f; border-bottom: 2px dotted #d9534f; cursor: help; font-weight: bold;">{word}</span>')
    
    html_all += f"""
    <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px;">
        <h3><a href="{art['url']}" target="_blank" style="text-decoration: none; color: #0056b3;">{art['title']}</a></h3>
        <p style="line-height: 1.8; color: #333;">{summary}</p>
        <p style="font-size: 0.8em; color: #888;">ソース: {art.get('source', {}).get('name')} | 公開: {art.get('publishedAt')}</p>
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
    <title>AIニュース要約</title>
</head>
<body style="background: #f8f9fa; font-family: 'Helvetica Neue', Arial, sans-serif; padding: 20px; max-width: 800px; margin: auto; color: #222;">
    <h1 style="text-align: center; color: #333;">📰 本日の厳選ニュース要約</h1>
    <p style="text-align: center; font-size: 0.9em; color: #666;">最終更新 (日本時間): {now}</p>
    {html_all}
    <footer style="text-align: center; margin-top: 50px; font-size: 0.8em; color: #999;">
        Powered by NewsAPI & Gemini API
    </footer>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)