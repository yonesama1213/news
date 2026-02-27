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
    """特定のカテゴリから最新の1記事を取得する"""
    url = f"https://news.google.com/rss/topics/{topic_id}?hl=ja&gl=JP&ceid=JP:ja"
    try:
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.text)
        item = root.find('.//item')
        if item is not None:
            return {
                'title': item.find('title').text,
                'link': item.find('link').text
            }
    except Exception as e:
        print(f"RSS取得エラー: {e}")
    return None

def summarize_with_gemini(title):
    """Geminiを使って要約と専門用語の抽出を行う"""
    prompt = f"""
    以下のニュースタイトルから内容を推測し、3文で要約してください。
    また、文中の専門用語や難しい言葉を最大3つ抽出し、その意味を解説してください。
    出力は必ず以下のJSON形式のみとし、余計な文章は含めないでください。
    {{
      "summary": "要約文1。要約文2。要約文3。",
      "glossary": [
        {{"word": "単語1", "def": "解説1"}},
        {{"word": "単語2", "def": "解説2"}}
      ]
    }}
    タイトル: {title}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        # JSON部分を抽出
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except Exception as e:
        print(f"Geminiエラー: {e}")
        return {"summary": "要約を生成できませんでした。", "glossary": []}

# --- メイン処理 ---
html_content = ""

for label, topic_id in TOPIC_IDS.items():
    print(f"{label} を取得中...")
    article = get_category_news(topic_id)
    
    if article:
        # Geminiで要約
        ai_data = summarize_with_gemini(article['title'])
        summary = ai_data.get('summary', '要約なし')
        
        # 専門用語をポップアップ(title属性)に置換
        for g in ai_data.get('glossary', []):
            word = g.get('word')
            definition = g.get('def')
            if word and definition:
                summary = summary.replace(word, f'<span class="term" title="{definition}">{word}</span>')
        
        html_content += f"""
        <div class="card">
            <div class="category-label">{label}</div>
            <h3><a href="{article['link']}" target="_blank">{article['title']}</a></h3>
            <p>{summary}</p>
        </div>
        """
        # APIのレート制限を考慮して少し待機
        time.sleep(1)

# 日本時間の取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

# HTML全体の組み立て
template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIニュース要約ダッシュボード</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; line-height: 1.6; }}
        .container {{ max-width: 800px; margin: auto; }}
        h1 {{ text-align: center; color: #1a73e8; margin-bottom: 10px; }}
        .update-time {{ text-align: center; font-size: 0.8em; color: #70757a; margin-bottom: 30px; }}
        .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; position: relative; }}
        .category-label {{ display: inline-block; background: #e8f0fe; color: #1967d2; font-size: 0.75em; font-weight: bold; padding: 4px 12px; border-radius: 20px; margin-bottom: 10px; }}
        h3 {{ margin: 0 0 15px 0; font-size: 1.25em; }}
        h3 a {{ color: #1a0dab; text-decoration: none; }}
        h3 a:hover {{ text-decoration: underline; }}
        p {{ margin: 0; color: #3c4043; }}
        .term {{ color: #d93025; border-bottom: 2px dotted #d93025; cursor: help; font-weight: bold; }}
        footer {{ text-align: center; margin-top: 50px; font-size: 0.8em; color: #70757a; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 AI News Summarizer</h1>
        <p class="update-time">最終更新（日本時間）: {now}</p>
        {html_content}
        <footer>© 2026 AI News Project - Powered by Google News RSS & Gemini API</footer>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)