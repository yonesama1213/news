import requests
import os
from datetime import datetime, timedelta, timezone

# 設定（GitHubのSecretsから読み込む）
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_news(category):
    # APIキーが入っているかチェック
    if not NEWS_API_KEY:
        print(f"⚠️ エラー: NEWS_API_KEY が読み込めていません！")
        return []

    # カテゴリなしの「日本全体のトップニュース」を取得するように一時的に変更
    url = f"https://newsapi.org/v2/everything?q=ニュース&language=jp&pageSize=5&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # GitHub ActionsのログにAPIの反応を詳しく出す
        print(f"--- API Response Log ---")
        print(f"Status Code: {response.status_code}")
        print(f"API Status: {data.get('status')}")
        
        if data.get("status") == "error":
            print(f"❌ APIエラーメッセージ: {data.get('message')}")
            return []
            
        articles = data.get('articles', [])
        print(f"✅ 取得できた記事数: {len(articles)}")
        return articles

    except Exception as e:
        print(f"❌ 通信エラーが発生しました: {e}")
        return []

# ニュース取得（カテゴリを問わず、まずは記事が出るか試す）
articles = get_news("all")
html_content = ""

if not articles:
    html_content = "<p style='color:red;'>【致命的】記事が1件も取得できませんでした。APIキーの設定や制限を確認してください。</p>"
else:
    for art in articles:
        html_content += f"""
        <div style="background:white; padding:10px; border-radius:5px; margin-bottom:10px;">
            <h3><a href="{art['url']}">{art['title']}</a></h3>
            <p>公開日時: {art.get('publishedAt')}</p>
        </div>"""

# 日本時間
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

template = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>デバッグ表示</title></head>
<body style="background:#f0f2f5; font-family:sans-serif; padding:20px;">
    <h1>🔍 NewsAPI 接続テスト</h1>
    <p>実行時刻: {now}</p>
    <div id="news-container">{html_content}</div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(template)