import streamlit as st
from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import json
import requests

# Setup
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]

st.set_page_config(page_title="Football Spanish Coach", layout="wide")
st.title("⚽ Football Spanish Coach")

# --- 1. Fetch & Select Match ---
with st.sidebar:
    st.header("📅 Select Match")
    # Fetching matches (using the FIFA World Cup ID 4429 as in your code)
    url = f"https://www.thesportsdb.com/api/v1/json/{FOOTBALL_API_KEY}/eventsnextleague.php?id=4429"
    response = requests.get(url)
    
    selected_event = None
    if response.status_code == 200 and response.json().get('events'):
        events = response.json()['events']
        # Create a dictionary for the selectbox to show friendly names
        event_options = {f"{e['strHomeTeam']} vs {e['strAwayTeam']} ({e['dateEvent']})": e for e in events}
        selected_name = st.selectbox("Choose a match to study:", options=list(event_options.keys()))
        selected_event = event_options[selected_name]
    else:
        st.write("No upcoming matches found.")

# --- 2. Study Options (Dynamic UI) ---
if selected_event:
    st.subheader(f"Studying: {selected_event['strEvent']}")
    
    # Study mode selection
    study_mode = st.radio(
        "What would you like to focus on?",
        ["Player/Coach Names", "Pre-Match Info", "In-Match Phrases"],
        horizontal=True
    )
    
    if st.button("Generate Study Content"):
        with st.spinner("Generating content..."):
            # Define prompts based on selection
            prompts = {
                "Player/Coach Names": f"List key players and coaches for {selected_event['strHomeTeam']} and {selected_event['strAwayTeam']}. Explain their roles.",
                "Pre-Match Info": f"Provide background info, team situations, and common media talking points for {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']}.",
                "In-Match Phrases": f"Provide 5 essential Spanish phrases for watching {selected_event['strHomeTeam']} vs {selected_event['strAwayTeam']} (e.g., scoring, corners). Return as JSON list of {{'es', 'en'}}."
            }
            
            prompt = prompts[study_mode]
            response = client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            
            # Display logic
            if study_mode == "In-Match Phrases":
                # JSON parsing logic here (same as before)
                st.session_state['phrases'] = json.loads(content.replace("```json", "").replace("```", ""))
            else:
                st.markdown(content)

# --- 3. Persistent Phrase Display ---
if 'phrases' in st.session_state:
    st.divider()
    st.header("Your Phrase List")
    for item in reversed(st.session_state['phrases']):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{item['es']}** — *{item['en']}*")
            tts = gTTS(text=item['es'], lang='es')
            fp = BytesIO()
            tts.write_to_fp(fp)
            col2.audio(fp, format="audio/mp3")