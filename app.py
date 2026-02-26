import streamlit as st
import json
import os

st.set_page_config(page_title="朝昼更新ニュース", layout="wide")
st.title("📰 定時更新：AIニュース掲示板")

if os.path.exists("latest_news.json"):
    with open("latest_news.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    st.success(f"✅ 最終更新：{data['updated_at']} （1日2回自動更新中）")
    
    tabs = st.tabs(list(data['categories'].keys()))
    for i, cat_name in enumerate(data['categories']):
        with tabs[i]:
            for item in data['categories'][cat_name]:
                with st.container(border=True):
                    st.subheader(item['title'])
                    st.caption(f"📍 {item['source']}")
                    st.markdown(item['summary'])
                    st.link_button("🌐 原文をチェック", item['link'])
else:
    st.warning("現在、初回のニュースデータを準備中です。しばらくお待ちください。")