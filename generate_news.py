import os
import json
import time
import feedparser
import urllib.parse
from datetime import datetime
from google import genai  # 最新のライブラリに変更

# カテゴリの名前（検索キーワード）
CATEGORIES = [
    "テクノロジー",
    "国内政治・社会",
    "環境・エネルギー",
    "国際情勢",
    "キャリア・働き方"
]

def main():
    # 環境変数からAPIキーを取得
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: API_KEY not found. $env:GEMINI_API_KEY='あなたのキー' を実行してください。")
        return

    # 最新のClientクラスを作成
    client = genai.Client(api_key=api_key)
    
    results = {
        "updated_at": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "categories": {}
    }

    for cat_name in CATEGORIES:
        print(f"検索中: {cat_name}...")
        try:
            # GoogleニュースからRSSを取得
            encoded_query = urllib.parse.quote(cat_name)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
            
            feed = feedparser.parse(rss_url)
            entries = feed.entries[:3]  # 上位3件を取得
            
            if not entries:
                print(f"  -> {cat_name}の記事が見つかりませんでした。")
                continue

            # AIへの依頼（プロンプト）作成
            titles_combined = "\n".join([f"- {e.title}" for e in entries])
            prompt = f"以下のニュースをそれぞれ3行の箇条書きで短く要約してください。各ニュースの間は '---' で区切ってください。要約のみ出力してください。\n{titles_combined}"
            
            # 最新の生成メソッド（Gemini 2.0 Flashを使用）
            response = client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            
            # 要約をリストに分割
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
            print(f"  -> {cat_name}の更新完了")
            time.sleep(1) # API制限を回避するための待機
            
        except Exception as e:
            print(f"Error in {cat_name}: {e}")

    # JSONファイルに保存
    with open("latest_news.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print("\n✨ 全カテゴリの更新が完了しました！")

if __name__ == "__main__":
    main()