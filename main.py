import requests
import google.generativeai as genai
import os
import json
from datetime import datetime, timedelta, timezone

# APIキーの設定
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_news(category_query):
    # 先ほど成功した everything エンドポイントを使って、カテゴリに関連する単語で検索します
    url = f"https://newsapi.org/v2/everything?q={category_query}&language=ja&pageSize=1&sortBy=relevancy&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    return response.json().get('articles', [])

def summarize_with_gemini(article):
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大3つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。
    {{"summary": "要約文1。要約文2。要約文3。", "glossary": [{{"word": "単語", "def": "解説"}}]}}

    タイトル: {article['title']}
    内容: {article.get('description', '') or article['title']}
    """
    try:
        response = model.generate_content(prompt)
        # JSON部分だけを抽出する安全な処理
        text = response.text
        start = text.find('{')
        end = text.rfind('}') + 1
        clean_json = text[start:end]
        return json.loads(clean_json)
    except:
        return {"summary": "要約に失敗しました。", "glossary": []}

# --- メイン処理 ---
categories = {"日本 政治": "国内情勢", "世界 ニュース": "世界情勢", "最新技術": "テクノロジー"}
html_all = ""

for query, label in categories.items():
    articles = get_news(query)
    if articles:
        art = articles[0] # 各カテゴリのトップ1記事
        ai_data = summarize_with_gemini(art)
        
        summary = ai_data['summary']
        for g in ai_data['glossary']:
            # 用語をポップアップ（title属性）付きのタグに変換
            summary = summary.replace(g['word'], f'<span class="term" title="{g["def"]}" style="color:blue; cursor:help; border-bottom:1px dotted;">{g["word"]}</span>')
        
        html_all += f"""
        <div style="background:white; padding:15px; margin-bottom:20px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
            <small>{label}</small>
            <h2><a href="{art['url']}" target="_blank">{art['title']}</a></h2>
            <p>{summary}</p>
        </div>
        """

# 日本時間
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>AIニュース要約</title></head>
<body style="background:#f0f2f5; font-family:sans-serif; padding:20px; max-width:700px; margin:auto;">
    <h1>📰 AIニュース要約（テスト版）</h1>
    <p>最終更新: {now}</p>
    {html_all}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)