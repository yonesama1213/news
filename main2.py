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
    1. 語尾は「〜です」「〜ます」とし、過度な話し言葉や子供っぽい表現は避けてください。
    2. ニュースの核心を正確に伝え、その背景や影響を客観的に述べてください。
    3. 難しい専門用語は、文脈の中で自然に補足するか、別の平易な言葉に置き換えてください。
    4. 全体で3文程度の簡潔な構成にしてください。
    5. 重要な語句を2つ選び、その定義（glossary）を丁寧な表現で作成してください。
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
    # タブボタンの生成
    active_btn = "active" if i == 0 else ""
    tab_buttons_html += f'<button class="tab-btn {active_btn}" onclick="showCategory(\'{label}\')">{label}</button>'
    
    # カテゴリごとのセクション
    display_style = "block" if i == 0 else "none"
    category_html = f'<div id="{label}" class="category-section" style="display:{display_style};">'
    
    url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP%3Aja"
    try:
        time.sleep(1)
        res = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:3]  # ✅ 各カテゴリ上位3件を取得
        
        for art in items:
            title, link = art.find('title').text, art.find('link').text
            ai_data = summarize_with_retry(title)
            
            content_html = ""
            if ai_data:
                summary = ai_data["summary"]
                for g in ai_data.get("glossary", []):
                    # 専門用語にホバーチップを適用
                    summary = summary.replace(g['word'], f'<span class="glossary-term" title="{g["def"]}">{g["word"]}</span>')
                content_html = f"<p>{summary}</p>"
            else:
                content_html = f"<p style='color:#666;'>※要約を取得できませんでした。</p>"

            category_html += f"""
            <div class="news-card">
                <h3 style="margin:10px 0;"><a href="{link}" target="_blank" style="text-decoration:none; color:#1a0dab;">{title}</a></h3>
                {content_html}
            </div>"""
    except Exception as e:
        print(f"RSS Error in {label}: {e}")
    
    category_html += "</div>"
    all_categories_html += category_html

# --- HTML テンプレート (CSSとJavaScriptを含む) ---
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AIニュースダッシュボード</title>
    <style>
        body {{ background:#f8f9fa; font-family:sans-serif; padding:20px; max-width:800px; margin:auto; color:#202124; }}
        h1 {{ border-left: 5px solid #1a73e8; padding-left: 15px; }}
        .tab-container {{ display: flex; gap: 8px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px; }}
        .tab-btn {{ padding: 10px 18px; border: none; border-radius: 20px; background: #e8eaed; cursor: pointer; white-space: nowrap; font-weight: bold; transition: 0.3s; }}
        .tab-btn.active {{ background: #1a73e8; color: white; }}
        .news-card {{ background:white; padding:20px; border-radius:12px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.05); border: 1px solid #dadce0; }}
        .glossary-term {{ color:#d93025; border-bottom:2px dotted; cursor:help; font-weight: bold; }}
        small {{ color: #5f6368; }}
    </style>
    <script>
        function showCategory(catId) {{
            // すべてのセクションを隠す
            document.querySelectorAll('.category-section').forEach(el => el.style.display = 'none');
            // すべてのボタンからactiveを消す
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            // 選択されたものだけ表示
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