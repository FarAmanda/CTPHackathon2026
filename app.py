import os
import json
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from Displayc_costar import apply_custom_theme, analyze_script_context

load_dotenv()

st.set_page_config(page_title="CoStar - Actor Rehearsal & Script Copilot", page_icon="🎭", layout="wide")
apply_custom_theme()

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# -------------------------------------------------------------
# Joe's Engine Functions (Chunking + Recitation)
# -------------------------------------------------------------
def chunk_line(text):
    prompt = f"""
You are helping a user memorize a line of text.
Break the supplied text into memorization chunks.

Rules:
1. Each chunk must contain no more than 10 words.
2. Chunks should ideally contain 6–10 words.
3. Prefer natural grammatical, semantic, and rhythmic boundaries.
4. Prefer chunks that form coherent phrases, clauses, or ideas.
5. Do not split a phrase unnecessarily just to reach 10 words.
6. A chunk may contain fewer than 6 words when necessary to preserve a natural phrase or because it is the end of the text.
7. Keep every word exactly as provided.
8. Do not correct spelling, grammar, punctuation, capitalization, contractions, or archaic language.
9. Do not add or remove any words.
10. Every word in the original text must appear exactly once in the chunks.
11. Return ONLY valid JSON.
12. The JSON must use exactly this format:
{{
    "chunks": [
        "first chunk",
        "second chunk",
        "third chunk"
    ]
}}

TEXT TO CHUNK:
{text}
"""
    interaction = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    return json.loads(interaction.text)

def evaluate_recitation(expected, spoken):
    prompt = f"""
Compare these two pieces of text for a memorization exercise.

EXPECTED:
{expected}

USER'S RESPONSE:
{spoken}

Determine whether the user's response matches the expected text.
Ignore: capitalization, punctuation, differences in whitespace.
Do NOT ignore: missing words, extra words, substituted words, words in the wrong order.
"""
    interaction = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "correct": {"type": "boolean"},
                    "mistakes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "expected": {"type": ["string", "null"]},
                                "heard": {"type": ["string", "null"]},
                                "type": {
                                    "type": "string",
                                    "enum": ["missing", "extra", "wrong_word", "wrong_order"]
                                }
                            },
                            "required": ["expected", "heard", "type"]
                        }
                    }
                },
                "required": ["correct", "mistakes"]
            }
        }
    )
    return json.loads(interaction.text)

# -------------------------------------------------------------
# Main Application Flow (Tabs)
# -------------------------------------------------------------
st.title("🎭 CoStar: Actor Script Engine")

tab_analysis, tab_flashcards, tab_recite = st.tabs([
    "📖 Script Context & Character Analysis",
    "📇 Step-by-Step Flashcards",
    "🎙️ Recitation & Memory Test"
])

# --- TAB 1: Script & Scene Interpretation (Web Search Grounded) ---
with tab_analysis:
    st.subheader("Deep Script Context & Performance Coaching")
    st.write("Gemini researches the play/film online to provide backstory, subtext, and delivery notes.")

    col1, col2 = st.columns(2)
    with col1:
        play_title = st.text_input("Play / Movie Title", placeholder="e.g., Hamlet, Succession, The Crucible")
    with col2:
        char_name = st.text_input("Character Name", placeholder="e.g., Hamlet, Kendall Roy, Abigail Williams")

    scene_input = st.text_area("Paste Scene Dialogue / Monologue", height=150, placeholder="Paste the lines here...")

    if st.button("Analyze Scene Subtext & Context", type="primary"):
        if not scene_input.strip():
            st.warning("Please provide lines to analyze.")
        else:
            with st.spinner("Searching script references and generating performance breakdown..."):
                analysis = analyze_script_context(client, play_title, char_name, scene_input)
                st.markdown(analysis)

# --- TAB 2: Flashcard Line Chunker ---
with tab_flashcards:
    st.subheader("Line Memorization Flashcards")
    st.write("Break down dense dialogue into digestible phrase-by-phrase flashcards.")

    fc_line = st.text_area("Dialogue to Memorize", height=100, placeholder="Enter dialogue here...", key="fc_input")
    
    if st.button("Chunk into Flashcards"):
        if not fc_line.strip():
            st.warning("Please enter some dialogue first.")
        else:
            with st.spinner("Chunking lines..."):
                res = chunk_line(fc_line)
                st.session_state.chunks = res["chunks"]
                st.session_state.card_idx = 0
                st.session_state.reveal = False

    if "chunks" in st.session_state and st.session_state.chunks:
        total = len(st.session_state.chunks)
        idx = st.session_state.card_idx

        st.progress((idx + 1) / total, text=f"Card {idx + 1} of {total}")
        
        with st.container(border=True):
            st.caption(f"PHRASE {idx + 1} / {total}")
            if st.session_state.get("reveal", False):
                st.markdown(f"### {st.session_state.chunks[idx]}")
            else:
                st.markdown("### ❓ *Recite phrase mentally, then flip...*")

        col_p, col_f, col_n = st.columns(3)
        with col_p:
            if st.button("⬅️ Previous", disabled=(idx == 0), use_container_width=True):
                st.session_state.card_idx -= 1
                st.session_state.reveal = False
                st.rerun()
        with col_f:
            flip_text = "🙈 Hide" if st.session_state.get("reveal", False) else "👁️ Reveal"
            if st.button(flip_text, use_container_width=True):
                st.session_state.reveal = not st.session_state.get("reveal", False)
                st.rerun()
        with col_n:
            if st.button("Next ➡️", disabled=(idx == total - 1), use_container_width=True):
                st.session_state.card_idx += 1
                st.session_state.reveal = False
                st.rerun()

# --- TAB 3: Joe's Recitation Test ---
with tab_recite:
    st.subheader("Real-Time Line Recitation Test")
    
    if "chunks" not in st.session_state or not st.session_state.chunks:
        st.info("Please chunk a line in the Flashcards tab first.")
    else:
        current_chunk = st.session_state.chunks[st.session_state.card_idx]
        st.write(f"Testing against **Chunk {st.session_state.card_idx + 1}**:")

        spoken = st.text_input("Type the line as you remember it:", key="recite_spoken_input")
        if st.button("Evaluate Recitation"):
            with st.spinner("Evaluating accuracy..."):
                eval_res = evaluate_recitation(current_chunk, spoken)
                if eval_res["correct"]:
                    st.success("Perfect recitation! 🎉")
                else:
                    st.error("Mistakes detected:")
                    for m in eval_res["mistakes"]:
                        st.write(f"- **{m['type'].upper()}**: Expected `{m['expected']}`, got `{m['heard']}`")