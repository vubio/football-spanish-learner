import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests
import random
import base64
import uuid

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
        [
            "Player/Coach Names", 
            "Pre-Match Info", 
            "In-Match Phrases", 
            "Tactical Analysis", 
            "Fan Slang", 
            "Referee & VAR"
        ],
        horizontal=True
    )
    
    if st.button("Generate Study Content"):
        with st.spinner("Crafting bite-sized lessons..."):
            
            # Contextual randomizers
            tactics = random.choice(["gegenpressing", "counter-attacking", "low-block defending", "possession-based build-up"])
            events = random.choice(["referee controversy", "corner kick routines", "yellow card pressure", "stoppage time drama"])
            
            prompts = {
                "Player/Coach Names": f"Identify exactly 8 key players or managers for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. For each figure, provide a name and exactly 1 short, simple Spanish sentence describing their role. Return ONLY JSON: [{{'topic': 'Name (Team)', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}].",
                
                "Pre-Match Info": f"Provide exactly 8 distinct, short tactical points or news items for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Keep descriptions strictly limited to 1 concise sentence. Return ONLY JSON: [{{'topic': 'Bite-sized Fact', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}].",
                
                "In-Match Phrases": f"Provide exactly 8 highly distinct, practical Spanish phrases tailored for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Keep each entry to exactly 1 short sentence. Return ONLY JSON: [{{'topic': 'Match Context', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}].",
                
                "Tactical Analysis": f"Provide exactly 8 advanced tactical football terms (e.g., formations, pressing, roles) relevant to a match between {selected_event['strHomeTeam']} and {selected_event['strAwayTeam']}. Provide the term and a 1-sentence definition. Return ONLY JSON: [{{'topic': 'Tactical Concept', 'es': '1 short analytical sentence in Spanish', 'en': 'English translation'}}].",
                
                "Fan Slang": f"Provide exactly 8 highly colloquial Spanish slang phrases or short chants that passionate fans of {selected_event['strHomeTeam']} or {selected_event['strAwayTeam']} might yell in the stadium. Keep it strictly to 1 short sentence. Return ONLY JSON: [{{'topic': 'Fan Emotion', 'es': '1 short slang sentence in Spanish', 'en': 'English translation'}}].",
                
                "Referee & VAR": f"Provide exactly 8 specific Spanish phrases related to referee decisions, VAR reviews, fouls, and offsides during {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Keep to 1 short sentence. Return ONLY JSON: [{{'topic': 'Rule/Decision', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}]."
            }
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    temperature=0.95,
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator. Do not include markdown backticks. You specialize in short, punchy language-learning cards. Keep the Spanish text extremely concise (maximum 1 clear sentence)."},
                        {"role": "user", "content": prompts[study_mode]}
                    ]
                )
                content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                
                # Parse JSON and immediately assign a permanent, unique UUID to each item
                parsed_data = json.loads(content)
                for item in parsed_data:
                    item['uid'] = str(uuid.uuid4())
                
                st.session_state['study_content'] = parsed_data
                st.session_state['current_mode'] = study_mode
                
            except Exception as e:
                st.error(f"Parsing error. Please click 'Generate Study Content' again to refresh.")

# 4. Universal Flashcard & Custom Speed Audio Display
if 'study_content' in st.session_state:
    st.divider()
    st.header(f"Study Cards: {st.session_state.get('current_mode', '')}")
    
    for item in st.session_state['study_content']:
        with st.container(border=True):
            st.subheader(item.get('topic', ''))
            col1, col2 = st.columns([4, 2])
            col1.write(f"**{item['es']}**")
            col1.caption(f"Meaning: {item['en']}")
            
            try:
                tts = gTTS(text=item['es'], lang='es')
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0) 
                
                b64_audio = base64.b64encode(fp.read()).decode()
                
                # Using the cryptographically unique ID ensures the browser NEVER caches the wrong audio
                unique_audio_id = f"audio_{item['uid']}"
                
                audio_html = f"""
                    <audio id="{unique_audio_id}" controls style="width: 100%;" 
                           onplay="this.playbackRate = 0.85;" 
                           onloadedmetadata="this.playbackRate = 0.85;">
                        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                    </audio>
                    <script>
                        var player = document.getElementById("{unique_audio_id}");
                        if (player) {{ player.playbackRate = 0.85; }}
                    </script>
                """
                col2.markdown(audio_html, unsafe_allow_html=True)
                
            except Exception as e:
                col2.error("Audio generation glitch")