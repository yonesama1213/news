import requests
import os
from datetime import datetime, timedelta, timezone
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if NEWS_API_KEY:
    print(f"使用中のキー: {NEWS_API_KEY[:3]}...{NEWS_API_KEY[-3:]}")
else:
    print("⚠️ NEWS_API_KEY が設定されていません")

def get_diagnostics():
    # 日本(jp)のトップニュースを取得
    url = f"https://newsapi.org/v2/top-headlines?country=jp&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        
        # 診断情報の作成
        diag = {
            "status_code": response.status_code,
            "api_status": data.get("status"),
            "total_results": data.get("totalResults"),
            "message": data.get("message", "No error message"),
            "articles_len": len(data.get("articles", []))
        }
        return diag, data.get("articles", [])
    except Exception as e:
        return {"error": str(e)}, []

# 診断実行
diag, articles = get_diagnostics()

html_content = ""
if not articles:
    html_content = f"""
    <div style="background:#ffebee; color:#c62828; padding:20px; border-radius:8px; border:2px solid #ef9a9a;">
        <h3>⚠️ ニュースが取得できませんでした</h3>
        <p><strong>原因のヒント:</strong></p>
        <ul>
            <li>HTTPステータス: {diag.get('status_code')}</li>
            <li>APIステータス: {diag.get('api_status')}</li>
            <li>ヒット件数: {diag.get('total_results')}</li>
            <li>エラー詳細: {diag.get('message')}</li>
        </ul>
        <p>※ヒット件数が 0 の場合、NewsAPI側で日本のニュースが一時的に止まっているか、無料制限がかかっています。</p>
    </div>
    """
else:
    # 記事がある場合は簡易表示
    for art in articles[:5]:
        html_content += f"<li>{art['title']}</li>"

# 日本時間
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>デバッグ画面</title></head>
<body style="font-family:sans-serif; padding:20px; max-width:600px; margin:auto;">
    <h1>🔍 接続診断モード</h1>
    <p>最終実行: {now}</p>
    {html_content}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)