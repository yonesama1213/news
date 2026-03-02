import os
from google import genai

# GitHub Secretsから読み込む（手元でテストする場合は直接書いてもOKですが、Push前に消してください）
api_key = os.getenv("GEMINI_API_KEY")

def test_connection():
    print("--- Gemini API 接続テスト開始 ---")
    
    if not api_key:
        print("❌ エラー: GEMINI_API_KEY が設定されていません。")
        return

    try:
        # クライアント初期化
        client = genai.Client(api_key=api_key)
        
        print(f"使用モデル: gemini-2.0-flash")
        
        # 最もシンプルなリクエスト
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="「接続成功」とだけ答えてください。"
        )
        
        if response.text:
            print(f"✅ 成功！ Geminiからの返答: {response.text.strip()}")
        else:
            print("⚠️ 応答はありましたが、テキストが空です。")
            
    except Exception as e:
        print(f"❌ 接続失敗: エラー内容を確認してください↓")
        print(f"--- エラー詳細 ---\n{e}\n------------------")

if __name__ == "__main__":
    test_connection()