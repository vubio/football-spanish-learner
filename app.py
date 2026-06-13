import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests

# 1. Setup Clients
# Ensure you have set your secrets in Streamlit Cloud: 
# OPENAI_API_KEY = "sk-..."
# FOOTBALL_API_KEY = "123" 
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football Spanish Coach")

# 2. Sidebar: Match Selection
with st.sidebar:
    st.header("📅 Select Match")
    # Using 4429 (FIFA World Cup) as an example. Change ID for other leagues.
    url = f"https://www.thesportsdb.com/api/v1/json/{FOOTBALL_API_KEY}/eventsnextleague.php?id=4429"
    
    selected_event = None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('events'):
                events = data['events']
                event_options = {f"{e['strHomeTeam']} vs {e['strAwayTeam']} ({e['dateEvent']})": e for e in events}
                selected_name = st.selectbox("Choose a match to study:", options=list(event_options.keys()))
                selected_event = event_options[selected_name]
            else:
                st.write("No upcoming matches found.")
        else:
            st.error("Could not fetch match data.")
    except Exception as e:
        st.error(f"API Error: {e}")

# 3. Main Area: Study Modes
if selected_event:
    st.subheader(f"Studying: {selected_event['strEvent']}")
    study_mode = st.radio(
        "Focus Area:",
        ["Player/Coach Names", "Pre-Match Info", "In-Match Phrases"],
        horizontal=True
    )
    
    if st.button("Generate Study Content"):
        with st.spinner("Generating content..."):
            prompts = {
                "Player/Coach Names": f"List key players and coaches for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Write a description for each IN SPANISH, followed by an English translation.",
                "Pre-Match Info": f"Provide pre-match team situations and talking points for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Write the response IN SPANISH, then provide an English summary.",
                "In-Match Phrases": f"Provide 5 essential Spanish phrases for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'es': 'Spanish phrase', 'en': 'English meaning'}}]."
            }
            
            response = client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompts[study_mode]}]
            )
            content = response.choices[0].message.content
            
            if study_mode == "In-Match Phrases":
                # Clean JSON string
                content = content.replace("```json", "").replace("```", "").strip()
                st.session_state['phrases'] = json.loads(content)
            else:
                st.markdown(content)

# 4. Phrase/Audio Display
if 'phrases' in st.session_state:
    st.divider()
    st.header("Spanish Phrase Cheat Sheet")
    for item in reversed(st.session_state['phrases']):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{item['es']}**")
            col1.caption(f"Meaning: {item['en']}")
            
            # --- AUDIO FIX ---
            tts = gTTS(text=item['es'], lang='es')
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0) # Rewind to start
            col2.audio(fp, format="audio/mp3")