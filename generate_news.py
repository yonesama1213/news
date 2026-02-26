from google import genai
import os
import json
import time
import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone

# --- 設定エリア ---
# GitHubのSecretsにある「GEMINI_API_KEY」を優先的に読み込み、なければ手入力のキーを使います
MY_API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyAe-_rEHe5VGbogwMlYm6cNpWdVMTMhMlA"

CATEGORIES = ["テクノロジー", "国内政治・社会", "環境・エネルギー", "国際情勢", "キャリア・働き方"]

def main():
    client = genai.Client(api_key=MY_API_KEY)
    jst = timezone(timedelta(hours=+9), 'JST')
    now_jst = datetime.now(jst)
    results = {"updated_at": now_jst.strftime("%Y/%m/%d %H:%M"), "categories": {}}

    for cat_name in CATEGORIES:
        print(f"検索中: {cat_name}...")
        try:
            encoded_query = urllib.parse.quote(cat_name)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
            feed = feedparser.parse(rss_url)
            
            # --- 【改善1】重複ニュースのフィルタリング ---
            seen_titles = set()
            unique_entries = []
            for e in feed.entries:
                # 記事タイトルの「 - 出版社名」より前の部分だけを取り出して比較
                clean_title = e.title.split(' - ')[0].strip()
                if clean_title not in seen_titles:
                    seen_titles.add(clean_title)
                    unique_entries.append(e)
                if len(unique_entries) >= 3: break # 3件見つかったら終了

            articles = []
            for entry in unique_entries:
                prompt = (
                    f"ニュースタイトル: {entry.title}\n"
                    "上記の内容を、重要なポイント3つの箇条書きで短く要約してください。\n"
                    "・先頭には「・」を使用してください。\n"
                    "・要約以外の文章は一切出力しないでください。"
                )
                
                summary = "要約の取得に失敗しました。"
                for attempt in range(3):
                    try:
                        response = client.models.generate_content(
                            model='gemini-2.0-flash', contents=prompt
                        )
                        summary = response.text.strip()
                        if summary: break
                    except Exception as e:
                        print(f"  AI呼び出し失敗(試行 {attempt+1}): {e}")
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
    print("\n✨ 全カテゴリのニュース生成に成功しました！")

if __name__ == "__main__":
    main()