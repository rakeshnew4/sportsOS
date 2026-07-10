"""LLM integration service using Groq for AI-powered features."""

import base64
import os
from typing import Optional

from groq import Groq

# Initialize Groq client from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    GROQ_API_KEY = None  # Will fail gracefully if not set


def get_groq_client() -> Groq:
    """Get or initialize Groq client."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable not set")
    return Groq(api_key=GROQ_API_KEY)


def llm_chat(
    prompt: str,
    system_prompt: str = "You are a helpful sports assistant for SportsOS, a sports court booking and matchmaking platform.",
    model: str = "mixtral-8x7b-32768",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Send a chat request to Groq.

    Args:
        prompt: User message/question
        system_prompt: System instruction for the model
        model: Groq model to use
        temperature: Creativity (0-2)
        max_tokens: Max response length

    Returns:
        Model's response text
    """
    try:
        client = get_groq_client()
        message = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return message.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq LLM: {e}")
        return None


def llm_chat_stream(
    prompt: str,
    system_prompt: str = "You are a helpful sports assistant for SportsOS.",
    model: str = "mixtral-8x7b-32768",
    temperature: float = 0.7,
    max_tokens: int = 1024,
):
    """
    Stream chat response from Groq (yields chunks).

    Args:
        prompt: User message
        system_prompt: System instruction
        model: Groq model
        temperature: Creativity level
        max_tokens: Max response length

    Yields:
        Response text chunks
    """
    try:
        client = get_groq_client()
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"Error streaming from Groq: {e}")
        yield None


def llm_with_image(
    prompt: str,
    image_path: str,
    system_prompt: str = "You are a helpful sports assistant for SportsOS.",
    model: str = "mixtral-8x7b-32768",
) -> str:
    """
    Send a prompt with an image to Groq (if model supports vision).

    Args:
        prompt: Text prompt
        image_path: Path to image file (or URL)
        system_prompt: System instruction
        model: Model to use (ensure it supports vision)

    Returns:
        Model's response
    """
    try:
        # If it's a local file, encode to base64
        if image_path.startswith(("http://", "https://")):
            image_content = {"type": "image_url", "image_url": {"url": image_path}}
        else:
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            image_ext = image_path.split(".")[-1].lower()
            mime_type = f"image/{image_ext}" if image_ext != "jpg" else "image/jpeg"
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{image_data}",
                },
            }

        client = get_groq_client()
        message = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        image_content,
                    ],
                },
            ],
            max_tokens=1024,
        )
        return message.choices[0].message.content
    except Exception as e:
        print(f"Error with image LLM: {e}")
        return None


def generate_recommendations(
    player_uid: str,
    player_history: dict,
    available_slots: list[dict],
) -> list[dict]:
    """
    Generate personalized match recommendations using LLM.

    Args:
        player_uid: Player ID
        player_history: Dict with player's history (sports, venues, skill level, etc)
        available_slots: List of available match slots

    Returns:
        List of recommended matches with scores
    """
    history_str = f"""
    Sports played: {', '.join(player_history.get('sports', []))}
    Favorite sport: {player_history.get('favorite_sport', 'N/A')}
    Skill level: {player_history.get('skill_level', 'intermediate')}
    Preferred time: {player_history.get('preferred_time', 'evening')}
    Frequent venues: {', '.join(player_history.get('venues', []))}
    """

    slots_str = "\n".join(
        [
            f"- {s['sport']} at {s['venue']} on {s['date']} {s['time']}, {s['players']}/{s['max_players']} filled"
            for s in available_slots[:5]
        ]
    )

    prompt = f"""Given this player's profile:
{history_str}

And these available match slots:
{slots_str}

Score each match 1-100 based on fit (sport match, time preference, venue familiarity, player count).
Return ONLY a JSON array with {{match_index, score, reason}}, no other text."""

    system_prompt = "You are a sports recommendation engine. Respond with valid JSON only, no markdown."

    response = llm_chat(prompt, system_prompt=system_prompt, max_tokens=512)
    if response:
        try:
            import json

            return json.loads(response)
        except:
            return []
    return []


def generate_team_name_suggestions(
    sport: str,
    player_name: str,
    num_suggestions: int = 5,
) -> list[str]:
    """
    Generate fun team name suggestions using LLM.

    Args:
        sport: Sport type (badminton, cricket, etc)
        player_name: Captain's name
        num_suggestions: How many to generate

    Returns:
        List of team name suggestions
    """
    prompt = f"""Generate {num_suggestions} fun, creative team names for a {sport} team captained by {player_name}.
Make them catchy and sports-related. Return ONLY a JSON array of strings, no other text.
Example: ["Thunder Rackets", "Net Ninjas", "Court Kings"]"""

    system_prompt = "You are a creative naming assistant. Respond with valid JSON array only."

    response = llm_chat(prompt, system_prompt=system_prompt, max_tokens=256)
    if response:
        try:
            import json

            return json.loads(response)
        except:
            return [f"{player_name}'s {sport.title()} Squad"]
    return [f"{player_name}'s {sport.title()} Squad"]


def generate_match_summary(
    match_data: dict,
) -> str:
    """
    Generate a human-friendly match summary using LLM.

    Args:
        match_data: Dict with match info (sport, venue, date, time, players, score, etc)

    Returns:
        Generated summary text
    """
    prompt = f"""Summarize this sports match in 2-3 sentences:
Sport: {match_data.get('sport', 'Unknown')}
Venue: {match_data.get('venue', 'Unknown')}
Date: {match_data.get('date', 'Unknown')}
Time: {match_data.get('time', 'Unknown')}
Players: {match_data.get('player_count', 0)}
Score: {match_data.get('score', 'TBD')}

Make it engaging and highlight the outcome."""

    system_prompt = "You are a sports commentator. Keep summaries concise and engaging."

    return llm_chat(prompt, system_prompt=system_prompt, max_tokens=256)


def generate_notification_message(
    event_type: str,
    event_data: dict,
) -> dict:
    """
    Generate personalized notification messages using LLM.

    Args:
        event_type: Type of event (match_formed, booking_reminder, team_invitation, etc)
        event_data: Event details (player_name, match_info, etc)

    Returns:
        Dict with title and body
    """
    prompts = {
        "match_formed": f"""Generate a fun push notification for a match that just formed.
Players: {event_data.get('players', 'Unknown')}
Sport: {event_data.get('sport', 'Unknown')}
Venue: {event_data.get('venue', 'Unknown')}
Time: {event_data.get('time', 'Unknown')}

Return ONLY JSON: {{"title": "...", "body": "..."}}""",
        "booking_reminder": f"""Generate a reminder notification for an upcoming booking.
Sport: {event_data.get('sport', 'Unknown')}
Venue: {event_data.get('venue', 'Unknown')}
Time in minutes: {event_data.get('minutes_until', 30)}

Return ONLY JSON: {{"title": "...", "body": "..."}}""",
        "team_invitation": f"""Generate an invitation notification.
Team: {event_data.get('team_name', 'Unknown')}
Invited by: {event_data.get('inviter', 'Unknown')}
Sport: {event_data.get('sport', 'Unknown')}

Return ONLY JSON: {{"title": "...", "body": "..."}}""",
    }

    prompt = prompts.get(event_type, prompts["match_formed"])
    system_prompt = "You are a sports notification writer. Respond with valid JSON only, no markdown."

    response = llm_chat(prompt, system_prompt=system_prompt, max_tokens=200)
    if response:
        try:
            import json

            return json.loads(response)
        except:
            return {"title": "SportsOS Update", "body": f"{event_type} event occurred"}
    return {"title": "SportsOS Update", "body": f"{event_type} event occurred"}


def analyze_player_skill(
    match_data: dict,
) -> dict:
    """
    Use LLM to analyze player skill level based on match performance.

    Args:
        match_data: Match results with player stats

    Returns:
        Dict with skill analysis for each player
    """
    prompt = f"""Analyze these players' performance in a {match_data.get('sport', 'game')}:
{str(match_data.get('player_stats', {}))}

Rate each player's apparent skill level (beginner/intermediate/advanced) with reasoning.
Return ONLY JSON: {{"player_uid": {{"skill": "...", "observation": "..."}}, ...}}"""

    system_prompt = "You are a sports skill analyst. Be fair and constructive."

    response = llm_chat(prompt, system_prompt=system_prompt, max_tokens=512)
    if response:
        try:
            import json

            return json.loads(response)
        except:
            return {}
    return {}
