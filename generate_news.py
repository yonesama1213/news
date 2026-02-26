from google import genai
import os
import json
import time
import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 設定エリア ---
MY_API_KEY = "AIzaSyAe-_rEHe5VGbogwMlYm6cNpWdVMTMhMlA" 
CATEGORIES = ["テクノロジー", "国内政治・社会", "環境・エネルギー", "国際情勢", "キャリア・働き方"]

def main():
    client = genai.Client(api_key=MY_API_KEY)
    
    # 日本時間の設定
    jst = timezone(timedelta(hours=+9), 'JST')
    now_jst = datetime.now(jst)
    results = {"updated_at": now_jst.strftime("%Y/%m/%d %H:%M"), "categories": {}}

    for cat_name in CATEGORIES:
        print(f"検索中: {cat_name}...")
        try:
            encoded_query = urllib.parse.quote(cat_name)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
            feed = feedparser.parse(rss_url)
            entries = feed.entries[:3]
            
            if not entries: continue

            articles = []
            for entry in entries:
                # 1件ずつ個別に要約を依頼（これが一番綺麗にまとまります）
                prompt = (
                    f"ニュースタイトル: {entry.title}\n"
                    "上記の内容を、重要なポイント3つの箇条書きで短く要約してください。\n"
                    "・先頭には「・」を使用してください。\n"
                    "・要約以外の文章は一切出力しないでください。"
                )
                
                summary = "要約の取得に失敗しました。"
                for attempt in range(3):
                    try:
                        # 接続確認が取れた「2.5-flash」を確実に使用
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', contents=prompt
                        )
                        summary = response.text.strip()
                        break
                    except Exception:
                        time.sleep(5)
                
                articles.append({
                    "title": entry.title, "link": entry.link,
                    "source": entry.source.get('title', '不明'), "summary": summary
                })
                time.sleep(1.5)

            results["categories"][cat_name] = articles
            print(f"  -> {cat_name}の更新完了")
            
        except Exception as e:
            print(f"Error in {cat_name}: {e}")

    with open("latest_news.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("\n✨ すべてのカテゴリのニュース生成に成功しました！")

if __name__ == "__main__":
    main()