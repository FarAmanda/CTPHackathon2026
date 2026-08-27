import os
import json

import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


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

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    return json.loads(interaction.output_text)


# -------------------------
# Streamlit UI
# -------------------------

st.title("🎭 Memorize Your Lines")

st.write(
    "Enter a line you'd like to memorize. "
    "Gemini will divide it into manageable memorization chunks."
)

line = st.text_area(
    "Your line",
    height=150,
    placeholder="Enter your line here..."
)


if st.button("Create Chunks"):

    if not line.strip():
        st.warning("Please enter a line first.")

    else:
        with st.spinner("Creating memorization chunks..."):

            result = chunk_line(line)

        st.session_state.chunks = result["chunks"]
        st.session_state.started = False


# -------------------------
# Display chunks
# -------------------------

if "chunks" in st.session_state:

    st.subheader("Your memorization chunks")

    for i, chunk in enumerate(
        st.session_state.chunks,
        start=1
    ):
        st.write(f"**Chunk {i}:** {chunk}")

# import os
# import json

# from dotenv import load_dotenv
# from google import genai

# load_dotenv()

# client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# text = "To be, or not to be, that is the question: Whether 'tis nobler in the mind to suffer The slings and arrows of outrageous fortune, Or to take arms against a sea of troubles And by opposing end them."

# def chunk_line(text):
#     prompt = f"""
# You are helping a user memorize a line of text.

# Break the supplied text into memorization chunks.

# Rules:
# 1. Each chunk must contain no more than 10 words.
# 2. Chunks should ideally contain 6–10 words.
# 3. Prefer natural grammatical, semantic, and rhythmic boundaries.
# 4. Prefer chunks that form coherent phrases, clauses, or ideas.
# 5. Do not split a phrase unnecessarily just to reach 10 words.
# 6. A chunk may contain fewer than 6 words when necessary to preserve a natural phrase or because it is the end of the text.
# 7. Keep every word exactly as provided.
# 8. Do not correct spelling, grammar, punctuation, capitalization, contractions, or archaic language.
# 9. Do not add or remove any words.
# 10. Every word in the original text must appear exactly once in the chunks.
# 11. Return ONLY valid JSON.
# 12. The JSON must use exactly this format:

# {{
#     "chunks": [
#         "first chunk",
#         "second chunk",
#         "third chunk"
#     ]
# }}

# TEXT TO CHUNK:
# {text}
# """

#     interaction = client.interactions.create(
#         model="gemini-3.6-flash",
#         input=prompt
#     )

#     return json.loads(interaction.output_text)


# # Test line
# line = (
#     "To be, or not to be, that is the question: "
#     "Whether 'tis nobler in the mind to suffer "
#     "The slings and arrows of outrageous fortune, "
#     "Or to take arms against a sea of troubles "
#     "And by opposing end them."
# )

# result = chunk_line(line)

# print("Gemini's chunks:")

# for i, chunk in enumerate(result["chunks"], start=1):
#     print(f"{i}. {chunk}")