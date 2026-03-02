import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- あなたのAPIキーで許可されているモデル一覧 ---")
try:
    # 許可されているモデルをすべて書き出す
    for m in client.models.list():
        print(f"許可済みID: {m.name}")
except Exception as e:
    print(f"リスト取得エラー: {e}")