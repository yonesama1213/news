import os
import json
import time
import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone
from google import genai

# --- 設定エリア ---
# GitHubのSecretsにある「GEMINI_API_KEY」を優先
MY_API_KEY = os.environ.get("GEMINI_API_KEY") or "あなたのAPIキー"

# カテゴリ設定
CATEGORIES = ["テクノロジー", "国内政治・社会", "環境・エネルギー", "国際情勢", "キャリア・働き方"]

# 使用するモデル名 (2026年現在の安定版に修正) [cite: 2026-02-26]
MODEL_NAME = 'gemini-2.0-flash'

def main():
    client = genai.Client(api_key=MY_API_KEY)
    jst = timezone(timedelta(hours=+9), 'JST')
    now_jst = datetime.now(jst)
    
    # 結果格納用
    results = {
        "updated_at": now_jst.strftime("%Y/%m/%d %H:%M"),
        "categories": {}
    }

    for cat_name in CATEGORIES:
        print(f"--- 検索中: {cat_name} ---")
        try:
            encoded_query = urllib.parse.quote(cat_name)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
            feed = feedparser.parse(rss_url)
            
            # --- 重複フィルタリングの強化 ---
            seen_titles = set()
            unique_entries = []
            for e in feed.entries:
                # タイトルから出版社名を除去し、記号をクリーニングして比較
                clean_title = e.title.split(' - ')[0].replace('【','').replace('】','').strip()
                
                # 先頭10文字が一致するか、既に含まれていればスキップ
                title_sig = clean_title[:10]
                if title_sig in seen_titles:
                    continue
                
                seen_titles.add(title_sig)
                unique_entries.append(e)
                if len(unique_entries) >= 3: break # 各カテゴリ3件

            articles = []
            for entry in unique_entries:
                prompt = (
                    f"ニュースタイトル: {entry.title}\n"
                    "上記の内容を、重要なポイント3つの箇条書きで短く要約してください。\n"
                    "・先頭には「・」を使用してください。\n"
                    "・要約以外の文章（「はい、わかりました」等）は一切出力しないでください。"
                )
                
                final_summary = None
                
                # 最大3回リトライ
                for attempt in range(3):
                    try:
                        response = client.models.generate_content(
                            model=MODEL_NAME, 
                            contents=prompt
                        )
                        text = response.text.strip()
                        
                        # 要約が空でなく、エラーメッセージを含まない場合のみ採用
                        if text and "失敗" not in text:
                            final_summary = text
                            break
                    except Exception as e:
                        print(f"  AI呼び出し失敗(試行 {attempt+1}): {e}")
                        time.sleep(5)
                
                # 正常に要約できた場合のみリストに追加
                if final_summary:
                    articles.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": entry.source.get('title', '不明'),
                        "summary": final_summary
                    })
                    print(f"  ✅ 成功: {entry.title[:20]}...")
                else:
                    print(f"  ❌ スキップ(要約失敗): {entry.title[:20]}...")
                
                # API負荷軽減のための待機
                time.sleep(1.5)

            # 記事が1件以上ある場合のみカテゴリを追加
            if articles:
                results["categories"][cat_name] = articles
            
        except Exception as e:
            print(f"Error in {cat_name}: {e}")

    # 最終的な保存処理
    if results["categories"]:
        with open("latest_news.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"\n✨ 生成完了: {len(results['categories'])} カテゴリの更新に成功しました。")
    else:
        print("\n⚠️ 警告: 有効なニュースデータが生成されなかったため、ファイルは更新しません。")

if __name__ == "__main__":
    main()