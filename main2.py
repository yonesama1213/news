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

CATEGORIES = {
    "国内情勢": "日本 政治 国内",
    "世界情勢": "国際 ニュース 世界",
    "ビジネス": "経済 ビジネス 市場",
    "テクノロジー": "IT テクノロジー AI",
    "教育・科学": "教育 科学 研究"
}

def summarize_with_gemini(title):
    """要約を生成する。失敗してもエラーで止めない。"""
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大2つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。余計な文章は一切不要です。
    {{"summary": "...", "glossary": [{{"word": "...", "def": "..."}}]}}
    タイトル: {title}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # --- 対策1: JSONの強制的抜き出し ---
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            return None
        
        return json.loads(text[start:end])
    except:
        return None # 失敗した場合はNoneを返す

# --- メイン処理 ---
html_content = ""
headers = {"User-Agent": "Mozilla/5.0"}

for label, query in CATEGORIES.items():
    url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    try:
        time.sleep(1) # 連続アクセス対策
        response = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(response.text)
        art = root.find('.//item') # 各カテゴリのトップ1記事のみ要約
        
        if art is not None:
            title = art.find('title').text
            link = art.find('link').text
            
            # --- 対策2: AI要約の実行と失敗時の処理 ---
            ai_data = summarize_with_gemini(title)
            
            if ai_data:
                summary = ai_data.get('summary', '要約を取得できませんでした。')
                # 専門用語の置換
                for g in ai_data.get('glossary', []):
                    word, definition = g.get('word'), g.get('def')
                    if word and definition:
                        summary = summary.replace(word, f'<span style="color:#d93025; border-bottom:2px dotted; cursor:help;" title="{definition}">{word}</span>')
                display_text = f"<p style='line-height:1.6;'>{summary}</p>"
            else:
                # AIが失敗した場合はタイトルをそのまま出す（サイトを壊さない）
                display_text = f"<p style='color:#666;'>※要約を生成中、または取得できませんでした。</p>"

            html_content += f"""
            <div style="background:white; padding:20px; border-radius:12px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                <small style="color:#1967d2; font-weight:bold;">{label}</small>
                <h3 style="margin:10px 0;"><a href="{link}" target="_blank" style="text-decoration:none; color:#1a0dab;">{title}</a></h3>
                {display_text}
            </div>"""

    except Exception as e:
        print(f"Error in {label}: {e}")

# 日本時間
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AIニュース要約</title></head>
<body style="background:#f8f9fa; font-family:sans-serif; padding:20px; max-width:800px; margin:auto;">
    <h1 style="text-align:center;">🗞️ AIニュース・ダッシュボード</h1>
    <p style="text-align:center; color:#666; font-size:0.8em;">最終更新: {now}</p>
    {html_content}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)