import streamlit as st
import requests

def ask_ai(prompt):
    """Refined Groq call to handle the dynamic response correctly"""
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7  # Adds a bit of 'personality' to the coach
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        res_json = response.json()

        # This is the line that fixes the 'choices' error
        if 'choices' in res_json and len(res_json['choices']) > 0:
            return res_json['choices'][0]['message']['content']
        else:
            return f"AI Error: {res_json.get('error', {}).get('message', 'Check API Key')}"
    except Exception as e:
        return f"Connection Error: {str(e)}"