import os
import json
import time
import feedparser
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# カテゴリの名前（これがそのまま検索キーワードになります）
CATEGORIES = [
    "テクノロジー",
    "国内政治・社会",
    "環境・エネルギー",
    "国際情勢",
    "キャリア・働き方"
]

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: API_KEY not found.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    results = {
        "updated_at": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "categories": {}
    }

    for cat_name in CATEGORIES:
        print(f"検索中: {cat_name}...")
        # カテゴリ名をURL用にエンコード
        encoded_query = urllib.parse.quote(cat_name)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
        
        feed = feedparser.parse(rss_url)
        entries = feed.entries[:3]
        titles = [e.title for e in entries]
        
        if not titles:
            continue

        # まとめ要約
        titles_combined = "\n".join([f"- {t}" for t in titles])
        prompt = f"以下のニュースをそれぞれ3行の箇条書きで短く要約してください。各ニュースの間は '---' で区切ってください。要約のみ出力してください。\n{titles_combined}"
        
        try:
            response = model.generate_content(prompt)
            summary_list = [s.strip() for s in response.text.split('---') if s.strip()]
            
            articles = []
            for i, entry in enumerate(entries):
                summary = summary_list[i] if i < len(summary_list) else "要約の取得に失敗しました。"
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": entry.source.get('title', '不明'),
                    "summary": summary
                })
            results["categories"][cat_name] = articles
            time.sleep(1) # Tier 1ならもっと速くても大丈夫ですが念のため
            
        except Exception as e:
            print(f"Error in {cat_name}: {e}")

    with open("latest_news.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("全カテゴリの更新が完了しました！")

if __name__ == "__main__":
    main()