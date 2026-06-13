import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests

# Initialize Clients
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football Spanish Coach")

# --- SIDEBAR: Live Scores & Schedule ---
with st.sidebar:
    st.header("📅 Live Match Center")
    
    # Add a slider to let you control how many matches to see
    num_matches = st.slider("Number of matches to display", 1, 20, 5)
    
    url = f"https://www.thesportsdb.com/api/v1/json/{FOOTBALL_API_KEY}/eventsnextleague.php?id=4429"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['events']:
            # Use the slider value here instead of a hardcoded number
            for event in data['events'][:num_matches]:
                st.write(f"**{event['strEvent']}**")
                # ... rest of your code
                st.caption(f"Date: {event['dateEvent']} | Time: {event['strTime']}")
                
                # Context button
                if st.button(f"Get Context for {event['strHomeTeam']}", key=event['idEvent']):
                    with st.spinner("Analyzing match context..."):
                        prompt = f"Give me 3 short, interesting facts or linguistic notes for a football match between {event['strHomeTeam']} and {event['strAwayTeam']} to help me learn Spanish."
                        context = client.chat.completions.create(
                            model="gpt-4o", messages=[{"role": "user", "content": prompt}]
                        ).choices[0].message.content
                        st.info(context)
        else:
            st.write("No upcoming matches found.")
    else:
        st.error("Could not fetch match data.")

# --- MAIN AREA: Language Learning ---
st.header("Spanish Phrase Generator")
scenario = st.selectbox("Match Scenario", ["General", "Goal Scored", "Referee Decision", "Player Action"])
level = st.radio("Difficulty", ["Basic", "Advanced"], horizontal=True)

if st.button("Generate Phrases"):
    prompt = f"Give me 5 {level} Spanish sentences related to '{scenario}' in a football match. Return ONLY a JSON list of objects with 'es' and 'en' keys."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": "You are a strict JSON generator."}, {"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        new_phrases = json.loads(content)
        st.session_state.setdefault('phrases', []).extend(new_phrases)
    except Exception as e:
        st.error(f"Error generating phrases: {e}")

# Display phrases
if 'phrases' in st.session_state:
    for item in reversed(st.session_state['phrases']):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{item['es']}**")
            col1.caption(f"Meaning: {item['en']}")
            
            # Simple Text-to-Speech
            tts = gTTS(text=item['es'], lang='es')
            fp = BytesIO()
            tts.write_to_fp(fp)
            col2.audio(fp, format="audio/mp3")