import os
import streamlit as st
import requests
import openai
import pandas as pd
import json
import io
import re


def apply_custom_css(css):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

css = """
body {
    background-color: green;
    font-family: Arial, sans-serif;
    color: lightgray;
}

h1 {
    color: #4a76a8;
}

.stButton>button {
    background-color: #4a76a8;
    color: white;
    font-weight: bold;
}

.st-progress-bar>div>div {
    background-color: #4a76a8;
}
"""

apply_custom_css(css)

# API Key
openai.api_key = "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"

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def extract_and_translate_words(text):
    max_tokens = 2048
    text_parts = list(chunks(text, max_tokens))
    
    word_list = []
    attempts = 0
    max_attempts = 3
    progress_increment = 1 / max_attempts
    estimated_wait_time_per_attempt = 10

    progress_bar = st.progress(0)
    remaining_text = st.empty()

    while attempts < max_attempts:
        for text_part in text_parts:
            prompt = f"Given the English text:\n\n{text_part}\n\nPlease extract important English words and idioms found in the text along with their Japanese translations. Try to extract words and idioms as many as possible in each sentence. Do not extract a proper noun"
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "system", "content": "You are a helpful assistant that extracts English words and idioms from a given text and translates them into Japanese."}, {"role": "user", "content": prompt}],
                "max_tokens": 2048,
                "n": 1,
                "stop": None,
                "temperature": 0.1,
                }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai.api_key}",
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
            response_dict = response.json()
            if "error" in response_dict:
                st.write(f"APIエラーが発生しました: {response_dict['error']['message']}")
            else:
                answer = response_dict["choices"][0]["message"]["content"].strip()
                word_list.extend([{"English": eng.lstrip('- ').strip(), "Japanese": re.sub(r'\s*\([^)]*\)', '', jpn)} for eng, jpn in (line.split(": ") for line in answer.split("\n") if ": " in line)])

            word_list_unique = list({tuple(w.items()) for w in word_list})
            word_list = [dict(w) for w in word_list_unique]

            if word_list:
                break

        attempts += 1
        progress = attempts * progress_increment
        progress_bar.progress(progress)

        remaining_percentage = (1 - progress) * 100
        remaining_time_estimate = (max_attempts - attempts) * estimated_wait_time_per_attempt
        remaining_text.write(f"Remaining percentage: {remaining_percentage:.0f}%, Estimated remaining time: {remaining_time_estimate:.0f} seconds")


    return word_list

def save_to_excel(df):
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="words")
        return buffer.getvalue()

st.title("Vocaburary App_test ver3")

text = st.text_area("英語のテキストを入力してください")

if text:
    st.write("単語を抽出中...")
    word_list = extract_and_translate_words(text)

    st.write("単語帳：")
    df = pd.DataFrame(word_list, columns=["English", "Japanese"])
    df = df.sort_values("English", key=lambda x: x.str.lower()).reset_index(drop=True)
    df.index = range(1, len(df) + 1)
    st.table(df)

    if st.button("エクセルファイルをダウンロード"):
        excel_data = save_to_excel(df)
        st.download_button(
            label="エクセルファイルをダウンロード",
            data=excel_data,
            file_name="word_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
