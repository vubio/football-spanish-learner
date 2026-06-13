import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests
import random
import base64

# 1. Setup Clients
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football Spanish Coach")

# 2. Sidebar: Match Selection
with st.sidebar:
    st.header("📅 Select Match")
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
        with st.spinner("Crafting diverse Spanish phrases..."):
            
            # --- NEW: Randomizers to ensure high diversity every click ---
            tactics = random.choice(["overlapping runs", "high pressing", "offside traps", "counter-attacks", "set pieces"])
            events = random.choice(["a controversial foul", "a missed penalty", "a stunning long-range goal", "a VAR review", "managerial frustration", "fans chanting"])
            
            # --- NEW: Lengthened output requirements and increased count to 7 ---
            prompts = {
                "Player/Coach Names": f"Identify 4 key figures (players/coaches) for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Provide highly detailed, varied descriptions highlighting their playstyle or recent form. Return ONLY JSON: [{{'topic': 'Name & Team', 'es': 'Detailed Spanish description (2-3 sentences)', 'en': 'English translation'}}].",
                "Pre-Match Info": f"Provide 4 diverse, in-depth talking points for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}, focusing on {tactics} or team form. Return ONLY JSON: [{{'topic': 'Short Title', 'es': 'Detailed Spanish description (2-3 sentences)', 'en': 'English translation'}}].",
                "In-Match Phrases": f"Provide 7 highly diverse, complex Spanish phrases for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Include emotional reactions to {events}, tactical observations, and common fan slang. Return ONLY JSON: [{{'topic': 'Context', 'es': 'Longer, expressive Spanish phrase', 'en': 'English meaning'}}]."
            }
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    temperature=0.9, # <-- Forces the AI to be less repetitive 
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator. Never output markdown formatting. Use highly varied, natural, and expressive Spanish vocabulary."},
                        {"role": "user", "content": prompts[study_mode]}
                    ]
                )
                content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                
                st.session_state['study_content'] = json.loads(content)
                st.session_state['current_mode'] = study_mode
                
            except Exception as e:
                st.error(f"Error generating content: {e}. Try clicking generate again.")

# 4. Universal Flashcard & Custom Audio Display
if 'study_content' in st.session_state:
    st.divider()
    st.header(f"Study Cards: {st.session_state.get('current_mode', '')}")
    
    # Use enumerate to give each audio player a unique ID
    for i, item in enumerate(st.session_state['study_content']):
        with st.container(border=True):
            st.subheader(item.get('topic', ''))
            col1, col2 = st.columns([4, 2]) # Widened col2 slightly to fit the custom player
            col1.write(f"**{item['es']}**")
            col1.caption(f"Meaning: {item['en']}")
            
            try:
                tts = gTTS(text=item['es'], lang='es')
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0) 
                
                # --- NEW: Convert audio to Base64 and inject HTML to force 0.85x speed ---
                b64_audio = base64.b64encode(fp.read()).decode()
                audio_id = f"audio_{i}"
                
                audio_html = f"""
                    <audio id="{audio_id}" controls style="width: 100%;">
                        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                    </audio>
                    <script>
                        document.getElementById("{audio_id}").playbackRate = 0.85;
                    </script>
                """
                # Render the custom HTML instead of using st.audio
                col2.markdown(audio_html, unsafe_allow_html=True)
                
            except Exception as e:
                col2.error("Audio error")