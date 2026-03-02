import os
from google import genai

def list_my_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ エラー: 環境変数 GEMINI_API_KEY が見つかりません。")
        return

    try:
        client = genai.Client(api_key=api_key)
        print("--- 利用可能なモデル一覧 ---")
        
        # 利用可能なモデルを取得して表示
        for model in client.models.list():
            # '2.5' や 'flash' が含まれるものに絞って表示すると見やすいです
            print(f"ID: {model.name}")
            
    except Exception as e:
        print(f"❌ 通信エラー: {e}")

if __name__ == "__main__":
    list_my_models()