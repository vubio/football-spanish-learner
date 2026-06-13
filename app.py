import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests
import random
from supabase import create_client, Client

# 1. Setup Clients & DB
st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football Spanish Coach")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

# Initialize Supabase
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    db_connected = True
except Exception:
    db_connected = False

# Replace your old get_flag function with this:
def get_team_badge(match, side='home'):
    # TheSportsDB returns the image URL directly in the match object
    badge_url = match.get('strHomeBadge') if side == 'home' else match.get('strAwayBadge')
    if badge_url:
        return f'<img src="{badge_url}" width="25">'
    return "⚽" # Fallback if no badge found

# Initialize session states
if 'selected_event' not in st.session_state:
    st.session_state['selected_event'] = None
if 'study_content' not in st.session_state:
    st.session_state['study_content'] = []

# 2. Sidebar: Match Selection with Flags
with st.sidebar:
    st.header("🏆 World Cup 2026")
    
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
                    st.info("Select a match below.")
                
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
                            home = match['strHomeTeam']
                            away = match['strAwayTeam']
                            # Add flags to the button text!
                            match_name = f"{get_team_badge(match, 'home')} {match['strHomeTeam']} vs {match['strAwayTeam']} {get_team_badge(match, 'away')}"
                            
                            if st.button(match_name, key=match['idEvent'], use_container_width=True):
                                st.session_state['selected_event'] = match
            else:
                st.write("No matches found.")
    except Exception as e:
        st.error("API Error")

selected_event = st.session_state['selected_event']

# 3. Main Area: Three Tabs
tab1, tab2, tab3 = st.tabs(["🌎 General Spanish", "⚔️ Match Study", "📚 My Vocab Bank"])

# --- TAB 1: General Study ---
with tab1:
    st.subheader("Everyday Football Vocabulary")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        general_mode = st.radio(
            "Focus Area:",
            ["Positions", "Common Actions", "Stadium & Fans", "Basic Rules", "Numbers & Stats", "Match Progression", "Emotions"],
            horizontal=True,
            key="gen_radio"
        )
    with col2:
        st.write("") 
        shuffle_gen = st.button("🔄 Shuffle", key="shuffle_gen", use_container_width=True)
    
    if st.session_state.get('last_general_mode') != general_mode or shuffle_gen:
        with st.spinner("Crafting cards..."):
            gen_prompts = {
                "Positions": "Provide 8 football positions. Return JSON: [{'topic': 'Position', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Common Actions": "Provide 8 common football verbs in context. Return JSON: [{'topic': 'Verb', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Stadium & Fans": "Provide 8 stadium/fan terms. Return JSON: [{'topic': 'Stadium Vocab', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Basic Rules": "Provide 8 basic rules/phases. Return JSON: [{'topic': 'Rule/Phase', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Numbers & Stats": "Provide 10 phrases involving stats (formations, scorelines, possession). Return JSON: [{'topic': 'Numbers & Stats', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Match Progression": "Provide 8 phrases about match stages (halftime, knockout, extra time). Return JSON: [{'topic': 'Match Stage', 'es': '1 short sentence in Spanish', 'en': 'English translation'}].",
                "Emotions": "Provide 8 phrases describing player/fan emotions. Return JSON: [{'topic': 'Emotion', 'es': '1 short sentence in Spanish', 'en': 'English translation'}]."
            }
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", temperature=0.9,
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator. No markdown. Max 1 clear Spanish sentence."},
                        {"role": "user", "content": gen_prompts[general_mode]}
                    ]
                )
                st.session_state['study_content'] = json.loads(response.choices[0].message.content.replace("```json", "").replace("```", "").strip())
                st.session_state['current_mode'] = general_mode
                st.session_state['last_general_mode'] = general_mode
            except Exception:
                st.error("Error generating. Try again.")

# --- TAB 2: Match-Specific Study ---
with tab2:
    if selected_event:
        st.subheader(f"Studying: {selected_event['strEvent']}")
        
        col1_m, col2_m = st.columns([5, 1])
        with col1_m:
            match_mode = st.radio(
                "Match Focus:",
                ["Player Names", "Pre-Match Info", "In-Match Phrases", "Tactical Analysis", "Fan Slang", "Referee & VAR"],
                horizontal=True,
                key="match_radio"
            )
        with col2_m:
            st.write("") 
            shuffle_match = st.button("🔄 Shuffle", key="shuffle_match", use_container_width=True)
        
        if st.session_state.get('last_match_mode') != match_mode or shuffle_match:
            with st.spinner("Crafting cards..."):
                match_prompts = {
                    "Player Names": f"Identify 8 key players for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. MUST start sentence with their exact name. Return JSON: [{{'topic': 'Name', 'es': '1 short Spanish sentence', 'en': 'English'}}].",
                    "Pre-Match Info": f"Provide 8 tactical points for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return JSON: [{{'topic': 'Fact', 'es': '1 short Spanish sentence', 'en': 'English'}}].",
                    "In-Match Phrases": f"Provide 8 distinct Spanish phrases for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return JSON: [{{'topic': 'Context', 'es': '1 short Spanish sentence', 'en': 'English'}}].",
                    "Tactical Analysis": f"Provide 8 tactical terms relevant to {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return JSON: [{{'topic': 'Tactic', 'es': '1 short Spanish sentence', 'en': 'English'}}].",
                    "Fan Slang": f"Provide 8 slang phrases for fans of {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return JSON: [{{'topic': 'Slang', 'es': '1 short Spanish sentence', 'en': 'English'}}].",
                    "Referee & VAR": f"Provide 8 phrases related to referee decisions during {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}. Return JSON: [{{'topic': 'Decision', 'es': '1 short Spanish sentence', 'en': 'English'}}]."
                }
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o", temperature=0.95,
                        messages=[
                            {"role": "system", "content": "You are a strict JSON generator. No markdown. Max 1 clear Spanish sentence."},
                            {"role": "user", "content": match_prompts[match_mode]}
                        ]
                    )
                    st.session_state['study_content'] = json.loads(response.choices[0].message.content.replace("```json", "").replace("```", "").strip())
                    st.session_state['current_mode'] = match_mode
                    st.session_state['last_match_mode'] = match_mode
                except Exception:
                    st.error("Error generating. Try again.")
    else:
        st.info("Select a match from the sidebar.")

# --- RENDER GENERATED FLASHCARDS (Tabs 1 & 2) ---
if st.session_state['study_content'] and st.session_state.get('current_mode'):
    st.divider()
    st.header(f"Cards: {st.session_state['current_mode']}")
    
    if not db_connected:
        st.warning("⚠️ Connect Supabase in Secrets to enable the 'Save to Bank' feature!")

    for i, item in enumerate(st.session_state['study_content']):
        with st.container(border=True):
            st.caption(item.get('topic', ''))
            col1, col2, col3 = st.columns([5, 2, 1])
            
            col1.markdown(f"### :blue[{item['es']}]")
            col1.write(f"*{item['en']}*")
            
            try:
                tts = gTTS(text=item['es'], lang='es')
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0) 
                col2.audio(fp, format="audio/mp3")
            except Exception:
                col2.error("Audio error")
                
            # --- SUPABASE SAVE BUTTON ---
            with col3:
                st.write("") # Alignment spacing
                if db_connected:
                    if st.button("💾 Save", key=f"save_{i}_{item['es'][:10]}"):
                        try:
                            supabase.table("vocab").insert({
                                "topic": item.get("topic", "General"),
                                "es": item["es"],
                                "en": item["en"],
                                "status": "to_learn"
                            }).execute()
                            st.toast("✅ Saved to Bank!")
                        except Exception as e:
                            st.error("Failed to save.")

# --- TAB 3: My Vocab Bank ---
with tab3:
    if not db_connected:
        st.info("Your saved vocabulary will appear here once Supabase is connected.")
    else:
        st.header("🗂️ Manage Your Vocabulary")
        
        # Search & Filters
        search_col, filter_col = st.columns([3, 2])
        search_query = search_col.text_input("🔍 Search phrases...")
        bucket = filter_col.selectbox("Filter by Bucket:", ["To Learn (to_learn)", "Learnt (learnt)", "Archived (archive)"])
        bucket_val = bucket.split("(")[1].replace(")", "")
        
        st.divider()
        
        # Fetch Data
        try:
            # Query the database
            query = supabase.table("vocab").select("*").eq("status", bucket_val)
            if search_query:
                query = query.ilike("es", f"%{search_query}%")
            
            response = query.execute()
            saved_cards = response.data
            
            if not saved_cards:
                st.write("No vocabulary found in this bucket.")
            
            # Display Saved Cards
            for card in saved_cards:
                with st.container(border=True):
                    st.caption(card['topic'])
                    c1, c2, c3 = st.columns([5, 2, 2])
                    
                    c1.markdown(f"#### :blue[{card['es']}]")
                    c1.write(f"*{card['en']}*")
                    
                    # Audio
                    tts = gTTS(text=card['es'], lang='es')
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0) 
                    c2.audio(fp, format="audio/mp3")
                    
                    # Actions / Reclassification
                    with c3:
                        if bucket_val != "to_learn":
                            if st.button("🔄 Move to 'To Learn'", key=f"tl_{card['id']}"):
                                supabase.table("vocab").update({"status": "to_learn"}).eq("id", card['id']).execute()
                                st.rerun()
                        if bucket_val != "learnt":
                            if st.button("✅ Mark Learnt", key=f"ml_{card['id']}"):
                                supabase.table("vocab").update({"status": "learnt"}).eq("id", card['id']).execute()
                                st.rerun()
                        if bucket_val != "archive":
                            if st.button("📦 Archive", key=f"ar_{card['id']}"):
                                supabase.table("vocab").update({"status": "archive"}).eq("id", card['id']).execute()
                                st.rerun()
                                
        except Exception as e:
            st.error(f"Database error: {e}")