import requests
import google.generativeai as genai
import os

# --- 設定（本来は環境変数を使いますが、まずは直接入力でテスト） ---
NEWS_API_KEY = "8f420153afc4432383558764541310d4"
GEMINI_API_KEY = "AIzaSyAJQshLjJQfEqRvbT9S-ITrT3GrSYbxKVI"

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_news(category):
    url = f"https://newsapi.org/v2/top-headlines?country=jp&category={category}&pageSize=2&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    return response.json().get('articles', [])

def summarize_article(title, description):
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大3つ抽出して解説してください。
    必ず以下の形式のJSONで出力して：
    {{"summary": "要約文", "glossary": [{{"word": "単語", "def": "解説"}}]}}

    タイトル: {title}
    内容: {description}
    """
    response = model.generate_content(prompt)
    return response.text

# 実行
categories = ["general", "technology", "business", "science"]
for cat in categories:
    print(f"--- カテゴリ: {cat} ---")
    articles = get_news(cat)
    for art in articles:
        summary_json = summarize_article(art['title'], art['description'])
        print(f"タイトル: {art['title']}")
        print(f"AI要約: {summary_json}\n")