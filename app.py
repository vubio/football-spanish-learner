import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests
import random
import base64

# 1. Setup Clients & Session State Caches
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

if 'gen_id' not in st.session_state:
    st.session_state['gen_id'] = 0

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
        with st.spinner("Crafting bite-sized lessons..."):
            # Increment generation ID to instantly burst browser audio cache
            st.session_state['gen_id'] += 1
            
            # Contextual randomizers to prevent repetitive responses
            tactics = random.choice(["gegenpressing", "counter-attacking transitions", "low-block defending", "wing-back overlaps"])
            events = random.choice(["referee controversy", "corner kick routines", "yellow card pressure", "stoppage time drama"])
            
            # Rigid instructions requiring EXACTLY 8 items and strict 1-2 sentence limits
            prompts = {
                "Player/Coach Names": f"Identify exactly 8 key players or managers for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. For each figure, provide a name and exactly 1 or 2 short, simple Spanish sentences describing their role or current form. Return ONLY JSON: [{{'topic': 'Name (Team)', 'es': '1-2 short sentences in Spanish', 'en': 'English translation'}}].",
                "Pre-Match Info": f"Provide exactly 8 distinct, short tactical points or news items for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']} focusing broadly on {tactics}. Keep descriptions strictly limited to 1 or 2 concise sentences. Return ONLY JSON: [{{'topic': 'Bite-sized Fact', 'es': '1-2 short sentences in Spanish', 'en': 'English translation'}}].",
                "In-Match Phrases": f"Provide exactly 8 highly distinct, practical Spanish phrases tailored for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Include realistic crowd expressions and commentary reactions regarding {events}. Keep each entry to exactly 1 short sentence. Return ONLY JSON: [{{'topic': 'Match Context', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}]."
            }
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    temperature=0.95, # High creativity to ensure structural variety
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator. Do not include markdown backticks. You specialize in short, punchy language-learning cards. Keep the Spanish text extremely concise (maximum 1-2 clear sentences)."},
                        {"role": "user", "content": prompts[study_mode]}
                    ]
                )
                content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                
                st.session_state['study_content'] = json.loads(content)
                st.session_state['current_mode'] = study_mode
                
            except Exception as e:
                st.error(f"Parsing error. Please click 'Generate Study Content' again to refresh.")

# 4. Universal Flashcard & Custom Speed Audio Display
if 'study_content' in st.session_state:
    st.divider()
    st.header(f"Study Cards: {st.session_state.get('current_mode', '')}")
    
    for i, item in enumerate(st.session_state['study_content']):
        with st.container(border=True):
            st.subheader(item.get('topic', ''))
            col1, col2 = st.columns([4, 2])
            col1.write(f"**{item['es']}**")
            col1.caption(f"Meaning: {item['en']}")
            
            try:
                # Generate clean audio payload
                tts = gTTS(text=item['es'], lang='es')
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0) 
                
                b64_audio = base64.b64encode(fp.read()).decode()
                # Unique ID combining generation round and index ensures zero audio mixing
                unique_audio_id = f"audio_{st.session_state['gen_id']}_{i}"
                
                # HTML5 player with multi-event JavaScript hooks to fiercely guarantee 0.85x playback speed
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