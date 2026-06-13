import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests
import random
from supabase import create_client, Client
from datetime import datetime

# 1. Setup Clients & DB
st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football & General Spanish Coach")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    db_connected = True
except Exception:
    db_connected = False

# --- FIFA Broadcast Codes ---
def get_team_code(team_name):
    name = team_name.strip().upper()
    codes = {
        "USA": "USA", "UNITED STATES": "USA", "BRAZIL": "BRA", "MEXICO": "MEX", 
        "SOUTH KOREA": "KOR", "JAPAN": "JPN", "GERMANY": "GER", "SPAIN": "ESP", 
        "FRANCE": "FRA", "ARGENTINA": "ARG", "ENGLAND": "ENG", "PORTUGAL": "POR", 
        "ITALY": "ITA", "NETHERLANDS": "NED", "BELGIUM": "BEL", "URUGUAY": "URU", 
        "CANADA": "CAN", "SAUDI ARABIA": "KSA", "QATAR": "QAT", "SWITZERLAND": "SUI", 
        "MOROCCO": "MAR", "PARAGUAY": "PAR", "CZECH REPUBLIC": "CZE", 
        "SOUTH AFRICA": "RSA", "HAITI": "HAI", "SCOTLAND": "SCO", 
        "CURAÇAO": "CUW", "IVORY COAST": "CIV", "COTE D'IVOIRE": "CIV", 
        "ECUADOR": "ECU", "AUSTRALIA": "AUS", "TURKEY": "TUR", "EGYPT": "EGY", 
        "TUNISIA": "TUN", "SWEDEN": "SWE", "CAPE VERDE": "CPV", 
        "BOSNIA-HERZEGOVINA": "BIH", "BOSNIA AND HERZEGOVINA": "BIH"
    }
    return codes.get(name, name[:3].upper())

# Initialize session states properly to avoid auto-generation bugs
if 'selected_event' not in st.session_state: st.session_state['selected_event'] = None
if 'study_content' not in st.session_state: st.session_state['study_content'] = []
if 'last_general_mode' not in st.session_state: st.session_state['last_general_mode'] = "Positions"
if 'last_match_mode' not in st.session_state: st.session_state['last_match_mode'] = "Player Names"

# --- Dynamic AI Topic Generator ---
def generate_dynamic_topics(domain):
    prompt = f"Brainstorm 3 highly specific, completely random, and creative scenarios for practicing {domain} Spanish vocabulary. Return ONLY a JSON list of exactly 3 strings. Keep them under 5 words."
    try:
        res = client.chat.completions.create(
            model="gpt-4o", 
            temperature=1.0, # High temperature for maximum creativity
            messages=[
                {"role": "system", "content": "You are a strict JSON generator. Return only a JSON array of 3 strings."},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(res.choices[0].message.content.replace("```json", "").replace("```", "").strip())
    except Exception:
        # Fallback just in case the AI glitches
        return ["Unexpected Event", "Daily Routine", "Travel Problems"]

# 2. Sidebar: Match Selection
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
                    if date not in matches_by_date: matches_by_date[date] = []
                    matches_by_date[date].append(e)
                
                st.divider()
                
                with st.container(height=600, border=False):
                    for date in sorted(matches_by_date.keys()):
                        st.markdown(f"#### 📅 {date}")
                        for match in matches_by_date[date]:
                            home = match['strHomeTeam'].strip()
                            away = match['strAwayTeam'].strip()
                            match_name = f"[{get_team_code(home)}] vs [{get_team_code(away)}] | {home} vs {away}"
                            
                            if st.button(match_name, key=match['idEvent'], use_container_width=True):
                                st.session_state['selected_event'] = match
            else:
                st.write("No matches found.")
    except Exception as e:
        st.error("API Error")

selected_event = st.session_state['selected_event']

# 3. Main Area: Four Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🌎 General", "⚔️ Match", "🎲 Random", "📚 Vocab Bank"])

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

# --- TAB 3: Random Study ---
with tab3:
    st.subheader("🎲 Random Vocabulary Generator")
    
    col_domain, col_r1, col_r2 = st.columns([2, 3, 1])
    
    with col_domain:
        domain = st.radio("Topic Domain:", ["Football", "General Spanish"], horizontal=True, key="random_domain")
    
    # Manage domain switching: fetch AI topics on first load or when switching domains
    if 'current_domain' not in st.session_state or st.session_state['current_domain'] != domain:
        with st.spinner(f"Brainstorming {domain} scenarios..."):
            st.session_state['random_topics'] = generate_dynamic_topics(domain)
        st.session_state['current_domain'] = domain
    
    with col_r1:
        selected_random_topic = st.radio("Select a Scenario:", st.session_state['random_topics'], horizontal=True)
        
    with col_r2:
        st.write("") # Spacing
        # The wired button!
        if st.button("🎲 Roll New Scenarios", use_container_width=True):
            with st.spinner("Brainstorming new topics..."):
                st.session_state['random_topics'] = generate_dynamic_topics(domain)
            st.rerun()
            
    col_style, col_diff = st.columns(2)
    with col_style:
        vocab_style = st.selectbox("Vocabulary Style:", ["Mixed", "Nouns", "Verbs", "Adjectives", "Idioms & Phrases"])
    with col_diff:
        difficulty = st.selectbox("Difficulty Level:", ["Easy (Beginner)", "Intermediate", "Hard (Advanced)"])
        
    if st.button("Generate Random Content", use_container_width=True):
        with st.spinner("Crafting random cards..."):
            
            context = f"related to football, focusing entirely on the scenario: '{selected_random_topic}'" if domain == "Football" else f"focusing entirely on the scenario: '{selected_random_topic}'"
            random_prompt = f"Provide exactly 8 {difficulty} Spanish {vocab_style} {context}. Return JSON: [{{'topic': '{selected_random_topic} ({vocab_style})', 'es': '1 short {difficulty} sentence in Spanish', 'en': 'English translation'}}]."
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", temperature=0.95,
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator. No markdown. Max 1 clear Spanish sentence."},
                        {"role": "user", "content": random_prompt}
                    ]
                )
                st.session_state['study_content'] = json.loads(response.choices[0].message.content.replace("```json", "").replace("```", "").strip())
                st.session_state['current_mode'] = f"Random: {selected_random_topic}"
            except Exception:
                st.error("Error generating. Try again.")


# --- RENDER GENERATED FLASHCARDS (Tabs 1, 2, & 3) ---
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
                
            with col3:
                st.write("") 
                if db_connected:
                    if st.button("💾 Save", key=f"save_{i}_{item['es'][:10]}"):
                        try:
                                supabase.table("vocab").insert({
                                    "topic": item.get("topic", "General"),
                                    "es": item["es"],
                                    "en": item["en"],
                                    "status": "to_learn",
                                    "created_at": datetime.now().strftime("%Y-%m-%d") # New!
                                }).execute()
                                st.toast("✅ Saved to Bank!")
                            except Exception as e:
                                st.error("Failed to save.")

# --- TAB 4: My Vocab Bank ---
BUCKETS = {
    "To Learn": "to_learn",
    "Easy": "easy",
    "Hard": "hard",
    "Easy-Learnt": "easy_learnt",
    "Hard-Learnt": "hard_learnt",
    "Impossible": "impossible",
    "Impossible-Learnt": "impossible_learnt",
    "Archived": "archive"
}

with tab4:
    if not db_connected:
        st.info("Your saved vocabulary will appear here once Supabase is connected.")
    else:
        st.header("🗂️ Manage Your Vocabulary")
        
        # 1. Fetch all data for filtering
        try:
            all_data = supabase.table("vocab").select("*").execute().data
            
            # Count buckets and dates dynamically
            status_counts = {val: 0 for val in BUCKETS.values()}
            date_counts = {}
            for row in all_data:
                # Count status
                s = row.get("status")
                if s in status_counts: status_counts[s] += 1
                # Count dates
                d = row.get("created_at", "2026-06-13")
                date_counts[d] = date_counts.get(d, 0) + 1
            
            # Create friendly dropdown labels
            display_to_val = {f"{name} ({status_counts.get(val, 0)})": val for name, val in BUCKETS.items()}
            date_options = {f"{d} ({count})": d for d, count in date_counts.items()}
            date_options["All Dates"] = "All"
            
            # 2. UI Filters
            col_search, col_bucket, col_date = st.columns([3, 2, 2])
            search_query = col_search.text_input("🔍 Search...")
            selected_bucket_display = col_bucket.selectbox("Bucket:", list(display_to_val.keys()))
            selected_date_display = col_date.selectbox("Date:", list(date_options.keys()))
            
            st.divider()
            
            # 3. Apply Filters
            bucket_val = display_to_val[selected_bucket_display]
            target_date = date_options[selected_date_display]
            
            query = supabase.table("vocab").select("*").eq("status", bucket_val)
            if target_date != "All":
                query = query.eq("created_at", target_date)
            if search_query:
                query = query.ilike("es", f"%{search_query}%")
                
            saved_cards = query.execute().data
            
            if not saved_cards:
                st.write("No vocabulary found.")
            
            for card in saved_cards:
                with st.container(border=True):
                    st.caption(f"{card['topic']} | Added: {card.get('created_at', 'N/A')}")
                    c1, c2, c3 = st.columns([5, 2, 2])
                    
                    c1.markdown(f"#### :blue[{card['es']}]")
                    c1.write(f"*{card['en']}*")
                    
                    # Audio
                    tts = gTTS(text=card['es'], lang='es')
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0) 
                    c2.audio(fp, format="audio/mp3")
                    
                    with c3:
                        current_status_name = list(BUCKETS.keys())[list(BUCKETS.values()).index(card['status'])]
                        new_status_name = st.selectbox(
                            "Move to:", list(BUCKETS.keys()),
                            index=list(BUCKETS.keys()).index(current_status_name),
                            key=f"status_{card['id']}"
                        )
                        if new_status_name != current_status_name:
                            supabase.table("vocab").update({"status": BUCKETS[new_status_name]}).eq("id", card['id']).execute()
                            st.rerun()
                            
        except Exception as e:
            st.error(f"Database error: {e}")