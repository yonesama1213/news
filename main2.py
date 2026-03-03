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
    "国内情勢": "日本 政治 国内",
    "世界情勢": "国際 ニュース 世界",
    "ビジネス": "経済 ビジネス 市場",
    "テクノロジー": "IT テクノロジー AI",
    "教育・科学": "教育 科学 研究"
}

def summarize_with_retry(title, max_retries=3):
    model_names = ["gemini-2.5-flash", "gemini-1.5-flash"]
    prompt = f"""
    あなたはニュース解説者として、複雑な出来事を高校生にも伝わるように整理して説明してください。
   【編集方針】
    1. 語尾は「〜です」「〜ます」とし、正確かつ客観的に述べてください。
    2. 全体で3文程度の簡潔な構成にしてください。

    【用語解説（glossary）の選定基準】
    - 解説する単語を **3つ〜4つ** に増やしてください。
    - **「日常語」は除外してください。**（例：『会社』『会議』『発表』『計画』などは解説不要）
    - **「社会、経済、科学、ITの専門用語」**や、高校の公共・地理歴史・理科などの教科書に出てくるような**「重要語句」**を優先的に選んでください。
    - その用語を知らないと、ニュースの本質が理解できないものを抽出してください。
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
                if data.get("summary"):
                    print(f"成功: {title[:15]}... ({i+1}回目)")
                    return data
        except Exception as e:
            print(f"試行 {i+1}回目 失敗: {e}")
        time.sleep(2)
    return None

# --- メイン処理 ---
tab_buttons_html = ""
all_categories_html = ""
headers = {"User-Agent": "Mozilla/5.0"}

for i, (label, query) in enumerate(CATEGORIES.items()):
    active_btn = "active" if i == 0 else ""
    tab_buttons_html += f'<button class="tab-btn {active_btn}" onclick="showCategory(\'{label}\')">{label}</button>'
    
    display_style = "block" if i == 0 else "none"
    category_html = f'<div id="{label}" class="category-section" style="display:{display_style};">'
    
    url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    try:
        time.sleep(1)
        res = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:3] 
        
        for art in items:
            title, link = art.find('title').text, art.find('link').text
            ai_data = summarize_with_retry(title)
            
            content_html = ""
            if ai_data:
                summary = ai_data["summary"]
                for g in ai_data.get("glossary", []):
                    # title属性ではなく、独自CSS用のdata-title属性を使用
                    summary = summary.replace(g['word'], f'<span class="glossary-term" data-title="{g["def"]}">{g["word"]}</span>')
                content_html = f"<p>{summary}</p>"
            else:
                content_html = f"<p style='color:#666;'>※要約を取得できませんでした。</p>"

            category_html += f"""
            <div class="news-card">
                <h3><a href="{link}" target="_blank">{title}</a></h3>
                {content_html}
            </div>"""
    except Exception as e:
        print(f"RSS Error in {label}: {e}")
    
    category_html += "</div>"
    all_categories_html += category_html

# --- HTML 生成 ---
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AIニュース解説</title>
    <style>
        body {{ background:#f8f9fa; font-family:sans-serif; padding:20px; max-width:800px; margin:auto; color:#202124; }}
        h1 {{ border-left: 5px solid #1a73e8; padding-left: 15px; }}
        .tab-container {{ display: flex; gap: 8px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px; }}
        .tab-btn {{ padding: 10px 18px; border: none; border-radius: 20px; background: #e8eaed; cursor: pointer; white-space: nowrap; font-weight: bold; transition: 0.3s; }}
        .tab-btn.active {{ background: #1a73e8; color: white; }}
        
        .news-card {{ background:white; padding:20px; border-radius:12px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.05); border: 1px solid #dadce0; }}
        .news-card h3 a {{ text-decoration:none; color:#1a0dab; }}

        /* 専門用語の吹き出しカスタマイズ */
        .glossary-term {{
            color:#d93025;
            border-bottom:2px dotted;
            cursor:help;
            font-weight: bold;
            position: relative;
            display: inline-block;
        }}

        .glossary-term::after {{
            content: attr(data-title);
            display: none;
            position: absolute;
            bottom: 130%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #333;
            color: #fff;
            padding: 12px 16px;
            border-radius: 8px;
            width: 260px;
            font-size: 1.1rem; /* ✅ 文字を大きく設定 */
            line-height: 1.6;
            z-index: 100;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}

        .glossary-term:hover::after {{
            display: block;
        }}
        
        small {{ color: #5f6368; }}
    </style>
    <script>
        function showCategory(catId) {{
            document.querySelectorAll('.category-section').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(catId).style.display = 'block';
            event.currentTarget.classList.add('active');
        }}
    </script>
</head>
<body>
    <h1>🗞️ AI要約ダッシュボード</h1>
    <p><small>最終更新: {now} (JST)</small></p>
    <div class="tab-container">{tab_buttons_html}</div>
    {all_categories_html}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)