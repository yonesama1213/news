from google import genai
import os

# 直接書き込んだキー、または環境変数から取得
api_key = "AIzaSyAe-_rEHe5VGbogwMlYm6cNpWdVMTMhMlA" 
client = genai.Client(api_key=api_key)

print("利用可能なモデル一覧:")
for model in client.models.list():
    print(f" - {model.name}")