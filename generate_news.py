from google import genai
import os
import json
import time
import feedparser
import urllib.parse
from datetime import datetime

# --- 設定エリア ---
# ご提示いただいた新しいAPIキーを直接書き込んでいます
MY_API_KEY = "AIzaSyAe-_rEHe5VGbogwMlYm6cNpWdVMTMhMlA" 

# 取得するニュースのカテゴリ
CATEGORIES = ["テクノロジー", "国内政治・社会", "環境・エネルギー", "国際情勢", "キャリア・働き方"]

def main():
    # 最新のGoogle Gen AI SDKを使用して接続
    client = genai.Client(api_key=MY_API_KEY)
    
    results = {
        "updated_at": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "categories": {}
    }

    for cat_name in CATEGORIES:
        print(f"検索中: {cat_name}...")
        try:
            # Googleニュースから最新記事の情報を取得
            encoded_query = urllib.parse.quote(cat_name)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
            feed = feedparser.parse(rss_url)
            entries = feed.entries[:3] # 各カテゴリ上位3件を取得
            
            if not entries:
                print(f"  -> {cat_name}の記事が見つかりませんでした。")
                continue

            articles = []
            for entry in entries:
                # 箇条書きを正確に守らせるための、記事1件ずつの依頼（プロンプト）
                prompt = (
                    f"ニュースタイトル: {entry.title}\n"
                    "上記の内容を、重要なポイント3つの箇条書きで短く要約してください。\n"
                    "・先頭には「・」を使用してください。\n"
                    "・各行は短く簡潔にしてください。\n"
                    "・要約以外の文章は一切出力しないでください。"
                )
                
                # --- 【混雑対策】リトライ（再試行）処理 ---
                summary = "要約の取得に失敗しました。"
                for attempt in range(3): # 最大3回までやり直す
                    try:
                        # 先生のアカウントで利用可能な最新モデル「2.5-flash」を使用
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', 
                            contents=prompt
                        )
                        summary = response.text.strip()
                        break # 成功したらリトライのループを抜ける
                    except Exception as e:
                        # 503（混雑中）エラーが出た場合は少し待ってから再挑戦
                        if "503" in str(e):
                            print(f"  (サーバー混雑中... 5秒待って再試行します {attempt+1}/3)")
                            time.sleep(5)
                        else:
                            print(f"  AI呼び出し中にエラー: {e}")
                            break
                
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": entry.source.get('title', '不明'),
                    "summary": summary
                })
                # Googleのサーバーを労わるための短い休憩時間
                time.sleep(1.5)

            results["categories"][cat_name] = articles
            print(f"  -> {cat_name}の全記事更新完了")
            
        except Exception as e:
            print(f"Error in {cat_name}: {e}")

    # JSONファイルに結果を保存（app.pyがこれを読み込みます）
    with open("latest_news.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print("\n✨ すべてのカテゴリのニュース生成に成功しました！")

if __name__ == "__main__":
    main()