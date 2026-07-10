# LLM Integration with Groq — Setup Guide

## Quick Start

### 1. Install Groq SDK
```bash
cd sportsOS
pip install -r requirements.txt
```

### 2. Set Your Groq API Key

**Option A: Environment Variable (.env file)**
```bash
# Create a .env file in the sportsOS directory
cp .env.example .env

# Edit .env and add your Groq API key
GROQ_API_KEY=your_actual_groq_key_here
```

**Option B: System Environment Variable**
```bash
# Linux/Mac
export GROQ_API_KEY=your_groq_key_here

# Windows PowerShell
$env:GROQ_API_KEY = "your_groq_key_here"
```

⚠️ **SECURITY**: Never commit your real API key to git. Always use `.env` files and add them to `.gitignore`.

### 3. Verify Setup
```python
from app.services.llm_service import get_groq_client

# This will raise an error if API key is not set
client = get_groq_client()
print("✅ Groq API connected!")
```

---

## Available LLM Functions

### 1. Basic Chat
```python
from app.services.llm_service import llm_chat

response = llm_chat(
    prompt="What's a good warm-up for badminton?",
    system_prompt="You are a sports coach.",
    temperature=0.7,
    max_tokens=500
)
print(response)
```

### 2. Streaming Chat (Real-time responses)
```python
from app.services.llm_service import llm_chat_stream

for chunk in llm_chat_stream("Tell me about tennis strategies"):
    print(chunk, end="", flush=True)
```

### 3. Chat with Images
```python
from app.services.llm_service import llm_with_image

response = llm_with_image(
    prompt="Analyze this court condition",
    image_path="./court.jpg",  # Local file or URL
    system_prompt="You are a court inspector."
)
print(response)
```

### 4. Smart Recommendations (LLM-powered)
```python
from app.services.recommendations_service import get_player_recommendations_with_llm

recommendations = get_player_recommendations_with_llm(db, player_uid, limit=5)
# Returns matches scored by LLM based on player profile
```

### 5. Generate Team Name Suggestions
```python
from app.services.llm_service import generate_team_name_suggestions

names = generate_team_name_suggestions(
    sport="badminton",
    player_name="Rakesh",
    num_suggestions=5
)
# Returns: ["Thunder Rackets", "Net Ninjas", ...]
```

### 6. Smart Notifications (LLM-powered)
```python
from app.services.notifications_service import notify_with_llm

notification_id = notify_with_llm(
    db,
    uid="player_123",
    event_type="match_formed",
    event_data={
        "players": 4,
        "sport": "badminton",
        "venue": "Sports Arena",
        "time": "6:00 PM"
    }
)
# Creates engaging, personalized notification
```

### 7. Match Summary Generation
```python
from app.services.llm_service import generate_match_summary

summary = generate_match_summary({
    "sport": "badminton",
    "venue": "Sports Arena",
    "date": "2026-07-09",
    "time": "6:00-7:00 PM",
    "player_count": 4,
    "score": "Team A won 21-15, 21-18"
})
# Returns: "In an exciting badminton match at Sports Arena..."
```

### 8. Player Skill Analysis
```python
from app.services.llm_service import analyze_player_skill

analysis = analyze_player_skill({
    "sport": "badminton",
    "player_stats": {
        "player_1": {"smash_accuracy": "85%", "net_play": "good"},
        "player_2": {"footwork": "fast", "consistency": "excellent"}
    }
})
# Returns skill assessments for each player
```

---

## Integration Examples

### Example 1: Recommend Matches with LLM
```python
from app.services.recommendations_service import get_player_recommendations_with_llm

@app.get("/api/recommendations/{player_uid}")
def get_smart_recommendations(player_uid: str, db: Client = Depends(get_db)):
    """LLM-powered match recommendations"""
    recs = get_player_recommendations_with_llm(db, player_uid, limit=5)
    return {"recommendations": recs}
```

### Example 2: Engaging Notifications
```python
from app.services.notifications_service import notify_with_llm

def on_match_formed(db, booking_id, matched_players, venue_name, sport):
    """Notify players with engaging LLM messages"""
    for uid in matched_players:
        notify_with_llm(
            db,
            uid=uid,
            event_type="match_formed",
            event_data={
                "sport": sport,
                "venue": venue_name,
                "booking_id": booking_id
            }
        )
```

### Example 3: Dynamic Team Names in Streamlit
```python
# In streamlit_app.py
from app.services.llm_service import generate_team_name_suggestions

suggested_names = generate_team_name_suggestions(
    sport=selected_sport,
    player_name=current_user_name,
    num_suggestions=5
)

team_name = st.selectbox(
    "Team name (or enter custom)",
    options=suggested_names + ["Custom name..."],
    key=f"team_name_{venue_id}"
)
```

### Example 4: Match Summaries for History
```python
from app.services.llm_service import generate_match_summary

def record_completed_match(db, booking):
    """Record match with AI-generated summary"""
    summary = generate_match_summary({
        "sport": booking.sport,
        "venue": booking.tenant_name,
        "date": booking.date,
        "time": f"{booking.start_time}-{booking.end_time}",
        "player_count": len(participants),
        "score": "TBD"  # Would come from match results
    })
    
    # Store in database
    db.collection("matches").document().set({
        "booking_id": booking.booking_id,
        "summary": summary,
        "created_at": datetime.now().isoformat()
    })
```

---

## Models Available

Groq supports multiple fast models:

- **mixtral-8x7b-32768** (default, balanced)
- **llama-3-70b-8192** (powerful, larger)
- **llama2-70b-4096** (legacy, but reliable)

Use them like:
```python
llm_chat(
    prompt="Your question",
    model="llama-3-70b-8192"  # Specify model
)
```

---

## Error Handling

All LLM functions gracefully fall back if the API is unavailable:

```python
# This won't crash if Groq is down
recommendations = get_player_recommendations_with_llm(db, uid)
# Returns rule-based recommendations as fallback

notification_id = notify_with_llm(db, uid, "match_formed", data)
# Uses generic message if LLM fails
```

---

## Rate Limits & Cost

**Groq Free Tier:**
- Fast inference (high rate limit)
- No authentication required beyond API key
- Great for development

**Tips to minimize costs:**
1. Use streaming for long responses
2. Keep prompts concise
3. Use smaller models when possible
4. Cache common prompts

---

## Troubleshooting

**"GROQ_API_KEY not set"**
- Ensure `.env` file is in the sportsOS directory
- Or set system environment variable
- Restart app after setting key

**"API connection failed"**
- Check your internet connection
- Verify API key is valid (test on groq.com)
- Check rate limits

**"Response is None or incomplete"**
- Increase `max_tokens` in the call
- Use a larger model
- Try streaming for long responses

---

## Testing LLM Functions

```bash
# Test basic LLM functionality
cd sportsOS
python3 -c "
from app.services.llm_service import llm_chat
response = llm_chat('Hello, what sport do you recommend?')
print(response)
"
```

---

## Next Steps

1. ✅ Set up API key in `.env`
2. ✅ Install groq with `pip install -r requirements.txt`
3. ✅ Integrate LLM functions into your app
4. ✅ Use streaming for better UX in Streamlit
5. ✅ Monitor API usage in Groq dashboard

---

## Resources

- [Groq Console](https://console.groq.com) — Manage API keys & view usage
- [Groq API Docs](https://console.groq.com/docs/speech-text) — Full API reference
- [LLM Service Code](./app/services/llm_service.py) — Implementation details
