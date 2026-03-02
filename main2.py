import requests
import xml.etree.ElementTree as ET
from google import genai  # 新しいライブラリ
import os
import json
import time
from datetime import datetime, timedelta, timezone

# 新しいクライアントの初期化
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CATEGORIES = {
    "国内情勢": "日本 政治 国内",
    "世界情勢": "国際 ニュース 世界",
    "ビジネス": "経済 ビジネス 市場",
    "テクノロジー": "IT テクノロジー AI",
    "教育・科学": "教育 科学 研究"
}

def summarize_with_retry(title, max_retries=3):
    # 最新モデルを指定
    model_names = ["gemini-1.5-flash", "models/gemini-1.5-flash"]
    prompt = f"""
    以下のニュースを3文で要約し、専門用語を最大2つ抽出して解説してください。
    必ず以下のJSON形式のみで返答してください。
    {{"summary": "...", "glossary": [{{"word": "...", "def": "..."}}]}}
    タイトル: {title}
    """
    
    for i in range(max_retries):
        try:
            # 新しいライブラリの呼び出し方
            response = client.models.generate_content(
                model=current_model,
                contents=prompt
            )

            if not response.text:
                continue

            text = response.text.strip()
            
            # JSON抽出
            start, end = text.find('{'), text.rfind('}') + 1
            if start != -1 and end != 0:
                data = json.loads(text[start:end])
                if data.get("summary"):
                    print(f"成功: {title[:15]}... ({i+1}回目)")
                    return data
        except Exception as e:
            print(f"試行 {i+1}回目 失敗: {e}")
        time.sleep(2)
    return None

# --- メイン処理 (RSS取得部分はそのまま) ---
html_content = ""
headers = {"User-Agent": "Mozilla/5.0"}

for label, query in CATEGORIES.items():
    url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    try:
        time.sleep(1)
        res = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(res.text)
        art = root.find('.//item')
        
        if art is not None:
            title, link = art.find('title').text, art.find('link').text
            ai_data = summarize_with_retry(title)
            
            if ai_data:
                summary = ai_data["summary"]
                for g in ai_data.get("glossary", []):
                    summary = summary.replace(g['word'], f'<span style="color:#d93025; border-bottom:2px dotted; cursor:help;" title="{g["def"]}">{g["word"]}</span>')
                content = f"<p>{summary}</p>"
            else:
                content = f"<p style='color:#666;'>※要約を取得できませんでした。</p>"

            html_content += f"""
            <div style="background:white; padding:20px; border-radius:12px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                <small style="color:#1967d2; font-weight:bold;">{label}</small>
                <h3 style="margin:10px 0;"><a href="{link}" target="_blank" style="text-decoration:none; color:#1a0dab;">{title}</a></h3>
                {content}
            </div>"""
    except Exception as e:
        print(f"RSS Error: {e}")

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
template = f"<html><body style='background:#f8f9fa; font-family:sans-serif; padding:20px; max-width:800px; margin:auto;'><h1>🗞️ AI要約ダッシュボード</h1><p>更新: {now}</p>{html_content}</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)