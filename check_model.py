import google.generativeai as genai

# あなたのキーをここに入れる
genai.configure(api_key="AIzaSyAJjhF6B0CjJlnvFFMlpaNzluIilcQpjnM")

print("--- 利用可能なモデル一覧 ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"エラーが発生しました: {e}")