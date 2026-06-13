import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Football Spanish Coach", page_icon="⚽")
st.title("⚽ Football Spanish Coach")

# Sidebar for controls
with st.sidebar:
    st.header("Settings")
    scenario = st.selectbox("Match Scenario", ["General", "Goal Scored", "Referee Decision", "Player Action"])
    level = st.radio("Difficulty", ["Basic", "Advanced"])

if st.button("Generate Phrases"):
    prompt = f"Give me 5 {level} Spanish sentences related to '{scenario}' in a football match. Return ONLY JSON format: [{{'es': '...', 'en': '...'}}]"
    
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "user", "content": prompt}]
    )
    
    new_phrases = json.loads(response.choices[0].message.content)
    # Add new phrases to the top of the list
    st.session_state.setdefault('phrases', []).extend(new_phrases)

# Display phrases
if 'phrases' in st.session_state:
    for item in reversed(st.session_state['phrases']):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{item['es']}**")
            col1.caption(f"Meaning: {item['en']}")
            
            tts = gTTS(text=item['es'], lang='es')
            fp = BytesIO()
            tts.write_to_fp(fp)
            col2.audio(fp, format="audio/mp3")