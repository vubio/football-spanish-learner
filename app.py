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

# Initialize session states
if 'selected_event' not in st.session_state:
    st.session_state['selected_event'] = None
if 'last_general_mode' not in st.session_state:
    st.session_state['last_general_mode'] = None
if 'last_match_mode' not in st.session_state:
    st.session_state['last_match_mode'] = None
if 'study_content' not in st.session_state:
    st.session_state['study_content'] = []

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
                
                if st.session_state['selected_event']:
                    st.success(f"**Active:** {st.session_state['selected_event']['strEvent']}")
                else:
                    st.info("Select a match below to unlock match-specific study.")
                
                matches_by_date = {}
                for e in events:
                    date = e['dateEvent']
                    if date not in matches_by_date:
                        matches_by_date[date] = []
                    matches_by_date[date].append(e)
                
                st.divider()
                
                with st.container(height=600, border=False):
                    for date in sorted(matches_by_date.keys()):
                        st.markdown(f"#### 📅 {date}")
                        for match in matches_by_date[date]:
                            match_name = f"{match['strHomeTeam']} vs {match['strAwayTeam']}"
                            if st.button(match_name, key=match['idEvent'], use_container_width=True):
                                st.session_state['selected_event'] = match
            else:
                st.write("No World Cup matches found for this season.")
        else:
            st.error("Could not fetch match data.")
    except Exception as e:
        st.error(f"API Error: {e}")

selected_event = st.session_state['selected_event']

# 3. Main Area: Tabs for General vs Match-Specific
tab1, tab2 = st.tabs(["🌎 General Football Spanish", "⚔️ Match-Specific Study"])

# --- TAB 1: General Study ---
with tab1:
    st.subheader("Everyday Football Vocabulary")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        general_mode = st.radio(
            "General Focus Area:",
            [
                "Positions & Roles", 
                "Common Actions", 
                "Stadium & Fans", 
                "Basic Rules",
                "Numbers & Stats",
                "Match Progression",
                "Emotions & Reactions"
            ],
            horizontal=True,
            key="gen_radio"
        )
    with col2:
        # Subtle shuffle button just in case they want fresh cards for the same topic
        st.write("") # Spacing
        shuffle_gen = st.button("🔄 Shuffle", key="shuffle_gen", use_container_width=True)
    
    # Auto-generate if the radio selection changed OR if shuffle was clicked
    if general_mode != st.session_state['last_general_mode'] or shuffle_gen:
        with st.spinner("Crafting general study cards..."):
            gen_prompts = {
                "Positions & Roles": "Provide exactly 8 football positions or roles. Return ONLY JSON: [{'topic': 'Position', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Common Actions": "Provide exactly 8 common football verbs used in context. Return ONLY JSON: [{'topic': 'Verb', 'es': '1 short example sentence in Spanish', 'en': 'English translation'}].",
                "Stadium & Fans": "Provide exactly 8 common nouns or phrases related to the stadium, the pitch, or the crowd. Return ONLY JSON: [{'topic': 'Stadium Vocab', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Basic Rules": "Provide exactly 8 basic football rules, calls, or match phases. Return ONLY JSON: [{'topic': 'Rule/Phase', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Numbers & Stats": "Provide exactly 10 Spanish phrases involving football numbers and statistics (e.g., shirt numbers, formations like 4-3-3, match results like 2-1, 60% possession ratio, number of shots, attendance figures). Return ONLY JSON: [{'topic': 'Numbers & Stats', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Match Progression": "Provide exactly 8 Spanish phrases about match stages and tournament progression (e.g., first half, second half, extra time, halftime break, early/late goals, group stage, knockout, advancing, eliminated, 3rd place). Return ONLY JSON: [{'topic': 'Match Stage', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Emotions & Reactions": "Provide exactly 8 Spanish phrases describing human interactions and emotions in football (e.g., player frustration, fan joy, global audience excitement, crying, celebrating). Return ONLY JSON: [{'topic': 'Emotion/Reaction', 'es': '1 short sentence in Spanish', 'en': 'English translation'}]."
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
                
                # Update trackers
                st.session_state['last_general_mode'] = general_mode
                st.session_state['last_match_mode'] = None 
            except Exception as e:
                st.error("Parsing error. Please click Shuffle again.")

# --- TAB 2: Match-Specific Study ---
with tab2:
    if selected_event:
        st.subheader(f"Studying: {selected_event['strEvent']}")
        
        col1_m, col2_m = st.columns([5, 1])
        with col1_m:
            match_mode = st.radio(
                "Match Focus Area:",
                ["Player/Coach Names", "Pre-Match Info", "In-Match Phrases", "Tactical Analysis", "Fan Slang", "Referee & VAR"],
                horizontal=True,
                key="match_radio"
            )
        with col2_m:
            st.write("") # Spacing
            shuffle_match = st.button("🔄 Shuffle", key="shuffle_match", use_container_width=True)
        
        # Auto-generate if the radio selection changed OR if shuffle was clicked
        if match_mode != st.session_state['last_match_mode'] or shuffle_match:
            with st.spinner("Crafting match-specific cards..."):
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
                            {"role": "user", "content": match_prompts[match_mode]}
                        ]
                    )
                    content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    st.session_state['study_content'] = json.loads(content)
                    st.session_state['current_mode'] = match_mode
                    
                    # Update trackers
                    st.session_state['last_match_mode'] = match_mode
                    st.session_state['last_general_mode'] = None 
                except Exception as e:
                    st.error("Parsing error. Please click Shuffle again.")
    else:
        st.info("Please select a match from the sidebar to use match-specific features.")

# 4. Universal Flashcard & Native Audio Display
if 'study_content' in st.session_state and st.session_state['study_content']:
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