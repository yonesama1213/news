import requests
import xml.etree.ElementTree as ET
from google import genai
import os
import json
import time
from datetime import datetime, timedelta, timezone

# クライアントの初期化
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# カテゴリ設定
CATEGORIES = {
    "国内": "日本 政治 国内",
    "国際": "国際 ニュース 世界",
    "経済": "経済 ビジネス 市場",
    "IT": "IT テクノロジー AI",
    "教育": "教育 科学 研究"
}

def summarize_with_retry(title, max_retries=3):
    model_names = ["gemini-2.5-flash", "gemini-1.5-flash"]
    prompt = f"""
    ニュース解説者として、高校生向けに短く解説してください。
    【ルール】
    1. 丁寧な言葉で、2文（最大でも3文）で要約してください。
    2. 重要な専門用語を2つ選び、定義（glossary）を作ってください。日常語は除外。
    必ず以下のJSON形式のみで返答してください。
    {{"summary": "...", "glossary": [{{"word": "...", "def": "..."}}]}}
    タイトル: {title}
    """
    for i in range(max_retries):
        current_model = model_names[i % len(model_names)]
        try:
            response = client.models.generate_content(model=current_model, contents=prompt)
            if not response.text: continue
            text = response.text.strip()
            start, end = text.find('{'), text.rfind('}') + 1
            if start != -1 and end != 0:
                data = json.loads(text[start:end])
                if data.get("summary"): return data
        except: pass
        time.sleep(2)
    return None

# --- メイン処理 ---
all_articles_html = ""
headers = {"User-Agent": "Mozilla/5.0"}

for label, query in CATEGORIES.items():
    url_target = f"https://news.google.com/rss/search?q={query}+when:24h&hl=ja&gl=JP&ceid=JP%3Aja"
    try:
        time.sleep(1)
        res = requests.get(url_target, headers=headers, timeout=15)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:2] # 各カテゴリ2件 = 合計10件
        
        if not items:
            url_all = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
            res = requests.get(url_all, headers=headers, timeout=15)
            root = ET.fromstring(res.text)
            items = root.findall('.//item')[:2]

        for art in items:
            title, link = art.find('title').text, art.find('link').text
            time.sleep(5) 
            ai_data = summarize_with_retry(title)
            
            if ai_data:
                summary = ai_data["summary"]
                for g in ai_data.get("glossary", []):
                    summary = summary.replace(g['word'], f'<span class="glossary-term" data-title="{g["def"]}">{g["word"]}</span>')
                
                all_articles_html += f"""
                <div class="news-card">
                    <div class="cat-tag">{label}</div>
                    <h3><a href="{link}" target="_blank">{title[:40]}...</a></h3>
                    <p>{summary}</p>
                </div>"""
    except Exception as e:
        print(f"Error in {label}: {e}")

# --- HTML 生成 ---
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI News 1-Page</title>
    <style>
        body {{ background:#f0f2f5; font-family:sans-serif; padding:15px; margin:0; color:#333; }}
        header {{ text-align:center; margin-bottom:15px; }}
        h1 {{ font-size: 1.4rem; margin:0; color:#1a73e8; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 12px; }}
        .news-card {{ background:#fff; padding:12px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); font-size:0.9rem; position:relative; }}
        .cat-tag {{ display:inline-block; background:#e8f0fe; color:#1a73e8; font-size:0.7rem; padding:2px 8px; border-radius:4px; font-weight:bold; }}
        h3 {{ font-size:0.95rem; margin:8px 0; line-height:1.3; }}
        h3 a {{ text-decoration:none; color:#1a0dab; }}
        p {{ margin:0; line-height:1.4; color:#444; }}
        .glossary-term {{ color:#d93025; border-bottom:1px dotted; cursor:help; font-weight:bold; }}
        .glossary-term::after {{
            content: attr(data-title); display:none; position:absolute; bottom:100%; left:5%; 
            background:#333; color:#fff; padding:8px; border-radius:5px; width:90%; font-size:0.85rem; z-index:10;
        }}
        .glossary-term:hover::after {{ display:block; }}
        @media (max-width: 400px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <header>
        <h1>🗞️ 本日のニュース要約</h1>
        <small>{now} 更新</small>
    </header>
    <div class="grid">
        {all_articles_html}
    </div>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)