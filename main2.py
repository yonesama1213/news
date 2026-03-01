import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import json
import time
import sys
print("実際に動いているパス:", sys.executable)
print("実際に動いているバージョン:", sys.version)
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

def summarize_with_retry(title, max_retries=3):
    """要約を最大 max_retries 回までやり直す"""
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大2つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。
    {{"summary": "...", "glossary": [{{"word": "...", "def": "..."}}]}}
    タイトル: {title}
    """
    
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # JSON部分を抽出
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                data = json.loads(text[start:end])
                # 要約が空でないか確認
                if data.get("summary"):
                    print(f"成功: {title[:20]}... (試行 {i+1}回目)")
                    return data
            
        except Exception as e:
            print(f"失敗: {title[:20]}... (試行 {i+1}回目): {e}")
        
        # 失敗した場合は2秒待ってから次へ（AIを落ち着かせる）
        time.sleep(2)
    
    return None # 3回やってもダメだった場合

# --- メイン処理 ---
html_content = ""
headers = {"User-Agent": "Mozilla/5.0"}

for label, query in CATEGORIES.items():
    url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(response.text)
        art = root.find('.//item')
        
        if art is not None:
            title = art.find('title').text
            link = art.find('link').text
            
            # --- ここでリトライ機能付きの要約を呼び出す ---
            ai_data = summarize_with_retry(title)
            
            if ai_data:
                summary = ai_data["summary"]
                # 専門用語置換
                for g in ai_data.get("glossary", []):
                    word, definition = g.get("word"), g.get("def")
                    if word and definition:
                        summary = summary.replace(word, f'<span style="color:#d93025; border-bottom:2px dotted; cursor:help;" title="{definition}">{word}</span>')
                content = f"<p>{summary}</p>"
            else:
                # 最終的にダメだった場合のみ警告を出す
                content = f"<p style='color:red;'>※このニュースの要約は作成できませんでした。</p>"

            html_content += f"""
            <div style="background:white; padding:20px; border-radius:12px; margin-bottom:20px; shadow:0 2px 8px rgba(0,0,0,0.05);">
                <small style="color:#1967d2;">{label}</small>
                <h3><a href="{link}">{title}</a></h3>
                {content}
            </div>"""

    except Exception as e:
        print(f"Error: {e}")

# 日本時間・テンプレート作成（以下、以前のコードと同じ）
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
template = f"<html><body style='background:#f8f9fa; font-family:sans-serif; padding:20px; max-width:800px; margin:auto;'><h1>🗞️ AI要約ダッシュボード</h1><p>更新: {now}</p>{html_content}</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)