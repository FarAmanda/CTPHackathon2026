import streamlit as st
import json
from google.genai import types

def apply_custom_theme():
    """Injects high-contrast, clean UI styling for scripts and analysis."""
    st.markdown(
        """
        <style>
        .stTextArea textarea {
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.95rem;
        }
        .analysis-card {
            background-color: #1a1e24;
            border-left: 4px solid #3b82f6;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 12px;
        }
        .flashcard-box {
            background-color: #1e293b;
            border: 2px solid #334155;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            min-height: 140px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 15px 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def analyze_script_context(client, play_or_movie_title: str, character_name: str, scene_text: str):
    """Uses Gemini 3.6 Flash with Search Grounding to research the script and provide performance coaching."""
    prompt = f"""
You are an expert acting coach and dramaturg analyzing a script scene.

SCRIPT / PRODUCTION: {play_or_movie_title}
CHARACTER BEING PERFORMED: {character_name}

SCENE EXCERPT:
\"\"\"
{scene_text}
\"\"\"

Tasks:
1. Search the web for context on '{play_or_movie_title}', particularly character '{character_name}' and this scene's context.
2. Provide:
   - **Dramatic Objective:** What does the character want in this moment?
   - **Subtext & Motivations:** What are they thinking beneath what they say?
   - **Performance / Vocal Tone:** Delivery notes, tempo, and emotional beats.
   - **Contextual References:** Explain any archaic terms, references, or historical background relevant to delivery.
"""
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return response.text
    except Exception as e:
        return f"Error during script analysis: {e}"