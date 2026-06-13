import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json

# Setup client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("⚽ Football Spanish Coach")

if st.button("Get New Phrases"):
    prompt = "Give me 5 diverse, short Spanish sentences for watching a football match. Include player actions or referee calls. Format as JSON: [ {'es': '...', 'en': '...'} ]"
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    
    phrases = json.loads(response.choices[0].message.content)
    st.session_state['phrases'] = phrases

if 'phrases' in st.session_state:
    for item in st.session_state['phrases']:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{item['es']}** — *{item['en']}*")
        
        tts = gTTS(text=item['es'], lang='es')
        fp = BytesIO()
        tts.write_to_fp(fp)
        col2.audio(fp, format="audio/mp3")