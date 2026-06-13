import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests

# 1. Setup Clients
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football Spanish Coach")

# 2. Sidebar: Match Selection
with st.sidebar:
    st.header("📅 Select Match")
    # Using 4429 (FIFA World Cup)
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
        with st.spinner("Breaking content into bite-sized audio..."):
            
            # --- NEW PROMPT STRUCTURE: Everything is strict JSON now ---
            prompts = {
                "Player/Coach Names": f"Identify 4 key figures (players/coaches) for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Name & Team', 'es': 'Short description in Spanish', 'en': 'English translation'}}].",
                "Pre-Match Info": f"Provide 4 key talking points or tactical situations for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Short Title', 'es': 'Spanish description', 'en': 'English translation'}}].",
                "In-Match Phrases": f"Provide 5 essential Spanish phrases for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Context', 'es': 'Spanish phrase', 'en': 'English meaning'}}]."
            }
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator. Do not include markdown formatting."},
                        {"role": "user", "content": prompts[study_mode]}
                    ]
                )
                content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                
                # Store the content and the mode title in session state
                st.session_state['study_content'] = json.loads(content)
                st.session_state['current_mode'] = study_mode
                
            except Exception as e:
                st.error(f"Error generating content: {e}. Try clicking generate again.")

# 4. Universal Flashcard & Audio Display
if 'study_content' in st.session_state:
    st.divider()
    st.header(f"Study Cards: {st.session_state.get('current_mode', '')}")
    
    # Render everything uniformly as bite-sized cards
    for item in st.session_state['study_content']:
        with st.container(border=True):
            st.subheader(item.get('topic', ''))
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{item['es']}**")
            col1.caption(f"Meaning: {item['en']}")
            
            # Short, dedicated audio for ONLY the Spanish text
            try:
                tts = gTTS(text=item['es'], lang='es')
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0) 
                col2.audio(fp, format="audio/mp3")
            except Exception as e:
                col2.error("Audio error")