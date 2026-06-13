import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests
import random

# 1. Setup Clients
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football Spanish Coach")

# Initialize session state for the selected match
if 'selected_event' not in st.session_state:
    st.session_state['selected_event'] = None

# 2. Sidebar: Match Selection (Scrollable & Grouped)
with st.sidebar:
    st.header("🏆 World Cup 2026 Matches")
    
    url = f"https://www.thesportsdb.com/api/v1/json/{FOOTBALL_API_KEY}/eventsseason.php?id=4429&s=2026"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('events'):
                events = data['events']
                
                # Active Selection Display
                if st.session_state['selected_event']:
                    st.success(f"**Active:** {st.session_state['selected_event']['strEvent']}")
                else:
                    st.info("Select a match below to unlock match-specific study.")
                
                # Group matches by date
                matches_by_date = {}
                for e in events:
                    date = e['dateEvent']
                    if date not in matches_by_date:
                        matches_by_date[date] = []
                    matches_by_date[date].append(e)
                
                st.divider()
                
                # Create a scrollable container of 600 pixels height
                with st.container(height=600, border=False):
                    for date in sorted(matches_by_date.keys()):
                        st.markdown(f"#### 📅 {date}")
                        for match in matches_by_date[date]:
                            match_name = f"{match['strHomeTeam']} vs {match['strAwayTeam']}"
                            
                            # Use buttons for each match that stretch full width
                            if st.button(match_name, key=match['idEvent'], use_container_width=True):
                                st.session_state['selected_event'] = match
                                
            else:
                st.write("No World Cup matches found for this season in the database.")
        else:
            st.error("Could not fetch match data.")
    except Exception as e:
        st.error(f"API Error: {e}")

# Assign the session state to the variable used by the rest of the app
selected_event = st.session_state['selected_event']

# 3. Main Area: Tabs for General vs Match-Specific
tab1, tab2 = st.tabs(["🌎 General Football Spanish", "⚔️ Match-Specific Study"])

# --- TAB 1: General Study ---
with tab1:
    st.subheader("Everyday Football Vocabulary")
    general_mode = st.radio(
        "General Focus Area:",
        ["Positions & Roles", "Common Actions (Verbs)", "Stadium & Fans", "Basic Rules"],
        horizontal=True,
        key="gen_radio"
    )
    
    if st.button("Generate General Content"):
        with st.spinner("Crafting general study cards..."):
            gen_prompts = {
                "Positions & Roles": "Provide exactly 8 football positions or roles (e.g., goalkeeper, striker, winger). For each, provide the term and a 1-sentence definition in Spanish. Return ONLY JSON: [{'topic': 'Position', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Common Actions (Verbs)": "Provide exactly 8 common football verbs (e.g., to shoot, to tackle, to pass) used in context. Return ONLY JSON: [{'topic': 'Verb', 'es': '1 short example sentence in Spanish', 'en': 'English translation'}].",
                "Stadium & Fans": "Provide exactly 8 common nouns or phrases related to the stadium, the pitch, or the crowd. Return ONLY JSON: [{'topic': 'Stadium Vocab', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Basic Rules": "Provide exactly 8 basic football rules, calls, or match phases (e.g., kick-off, halftime, throw-in). Return ONLY JSON: [{'topic': 'Rule/Phase', 'es': '1 short sentence in Spanish', 'en': 'English translation'}]."
            }
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    temperature=0.9,
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator. Do not include markdown backticks. Keep the Spanish text extremely concise (maximum 1 clear sentence)."},
                        {"role": "user", "content": gen_prompts[general_mode]}
                    ]
                )
                content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                st.session_state['study_content'] = json.loads(content)
                st.session_state['current_mode'] = general_mode
            except Exception as e:
                st.error("Parsing error. Please click Generate again.")

# --- TAB 2: Match-Specific Study ---
with tab2:
    if selected_event:
        st.subheader(f"Studying: {selected_event['strEvent']}")
        study_mode = st.radio(
            "Match Focus Area:",
            ["Player/Coach Names", "Pre-Match Info", "In-Match Phrases", "Tactical Analysis", "Fan Slang", "Referee & VAR"],
            horizontal=True,
            key="match_radio"
        )
        
        if st.button("Generate Match Content"):
            with st.spinner("Crafting match-specific cards..."):
                tactics = random.choice(["gegenpressing", "counter-attacking", "low-block defending", "possession-based build-up"])
                events = random.choice(["referee controversy", "corner kick routines", "yellow card pressure", "stoppage time drama"])
                
                match_prompts = {
                    "Player/Coach Names": f"Identify exactly 8 key players or managers for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. You MUST start the Spanish sentence with the person's exact name (e.g., 'Neymar es...'). Return ONLY JSON: [{{'topic': 'Name (Team)', 'es': '1 short sentence in Spanish starting with their name', 'en': 'English translation'}}].",
                    "Pre-Match Info": f"Provide exactly 8 short tactical points for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Fact', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}].",
                    "In-Match Phrases": f"Provide exactly 8 distinct Spanish phrases for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Context', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}].",
                    "Tactical Analysis": f"Provide exactly 8 advanced tactical football terms relevant to {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Tactic', 'es': '1 short analytical sentence in Spanish', 'en': 'English translation'}}].",
                    "Fan Slang": f"Provide exactly 8 colloquial Spanish slang phrases for fans of {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Slang', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}].",
                    "Referee & VAR": f"Provide exactly 8 specific Spanish phrases related to referee decisions during {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return ONLY JSON: [{{'topic': 'Decision', 'es': '1 short sentence in Spanish', 'en': 'English translation'}}]."
                }
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        temperature=0.95,
                        messages=[
                            {"role": "system", "content": "You are a strict JSON generator. Do not include markdown backticks. Keep the Spanish text extremely concise (maximum 1 clear sentence)."},
                            {"role": "user", "content": match_prompts[study_mode]}
                        ]
                    )
                    content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    st.session_state['study_content'] = json.loads(content)
                    st.session_state['current_mode'] = study_mode
                except Exception as e:
                    st.error("Parsing error. Please click Generate again.")
    else:
        st.info("Please select a match from the sidebar to use match-specific features.")

# 4. Universal Flashcard & Native Audio Display
if 'study_content' in st.session_state:
    st.divider()
    st.header(f"Study Cards: {st.session_state.get('current_mode', '')}")
    
    for item in st.session_state['study_content']:
        with st.container(border=True):
            st.caption(f"{item.get('topic', '')}")
            
            col1, col2 = st.columns([4, 2])
            
            col1.markdown(f"### :blue[{item['es']}]")
            col1.write(f"*{item['en']}*")
            
            try:
                tts = gTTS(text=item['es'], lang='es')
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0) 
                
                col2.audio(fp, format="audio/mp3")
            except Exception as e:
                col2.error("Audio generation glitch")