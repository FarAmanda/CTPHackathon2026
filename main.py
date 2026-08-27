import os
import json
import time

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

def evaluate_recitation(expected, spoken):
    prompt = f"""
Compare these two pieces of text for a memorization exercise.

EXPECTED:
{expected}

USER'S RESPONSE:
{spoken}

Determine whether the user's response matches the expected text.

Ignore:
- capitalization
- punctuation
- differences in whitespace

Do NOT ignore:
- missing words
- extra words
- substituted words
- words in the wrong order
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": {
                "type": "object",
                "properties": {
                    "correct": {
                        "type": "boolean"
                    },
                    "mistakes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "expected": {
                                    "type": ["string", "null"]
                                },
                                "heard": {
                                    "type": ["string", "null"]
                                },
                                "type": {
                                    "type": "string",
                                    "enum": [
                                        "missing",
                                        "extra",
                                        "wrong_word",
                                        "wrong_order"
                                    ]
                                }
                            },
                            "required": [
                                "expected",
                                "heard",
                                "type"
                            ]
                        }
                    }
                },
                "required": [
                    "correct",
                    "mistakes"
                ]
            }
        }
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
        st.session_state.reveal_start = None
        st.session_state.submitted = False
        st.session_state.result = None


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

    st.divider()

    # if st.button("Start Memorizing"):

    #     st.session_state.started = True
    #     st.session_state.reveal_start = time.time()
    #     st.session_state.submitted = False
    #     st.session_state.result = None
    #     st.rerun()


# -------------------------
# Start memorization
# -------------------------

if st.button("Start Memorizing"):

    st.session_state.started = True
    st.session_state.current_index = len(st.session_state.chunks) - 1
    st.session_state.reveal_start = time.time()
    st.session_state.phase = "reveal"
    st.session_state.submitted = False
    st.session_state.result = None

    if "recitation_input" in st.session_state:
        del st.session_state["recitation_input"]

    st.rerun()


# -------------------------
# Memorization loop
# -------------------------

if st.session_state.get("started", False):

    chunks = st.session_state.chunks
    current_index = st.session_state.current_index

    # Everything from current_index through the end
    current_target = " ".join(chunks[current_index:])

    # -------------------------
    # Reveal phase
    # -------------------------

    if st.session_state.phase == "reveal":

        elapsed = time.time() - st.session_state.reveal_start

        if elapsed < 5:

            remaining = 5 - int(elapsed)

            st.subheader("Memorize this:")

            st.markdown(
                f"### {current_target}"
            )

            st.write(f"Starting in {remaining}...")

            time.sleep(0.1)
            st.rerun()

        else:

            st.session_state.phase = "recite"

            st.rerun()


    # -------------------------
    # Recitation phase
    # -------------------------

    elif st.session_state.phase == "recite":

        st.subheader("Your turn")

        st.write(
            "Type what you just memorized:"
        )

        response = st.text_input(
            "Recite the line",
            key="recitation_input"
        )

        if st.button("Check Answer"):

            if not response.strip():

                st.warning("Please enter your response.")

            else:

                with st.spinner("Checking your answer..."):

                    result = evaluate_recitation(
                        current_target,
                        response
                    )

                st.session_state.result = result
                st.session_state.submitted = True

                st.rerun()


# -------------------------
# Results
# -------------------------

if st.session_state.get("submitted", False):

    result = st.session_state.result

    if result["correct"]:

        st.success("Correct! 🎉")

        # Are there more chunks to learn?
        if st.session_state.current_index > 0:

            if st.button("Continue"):

                # Move one chunk earlier.
                #
                # Example:
                # 4 -> 3
                # 3 -> 2
                # 2 -> 1
                # 1 -> 0
                #
                # The target is then automatically:
                #
                # chunk 4
                # ↓
                # chunk 3 + chunk 4
                # ↓
                # chunk 2 + chunk 3 + chunk 4
                # etc.

                st.session_state.current_index -= 1

                st.session_state.reveal_start = time.time()
                st.session_state.phase = "reveal"
                st.session_state.submitted = False
                st.session_state.result = None

                if "recitation_input" in st.session_state:
                    del st.session_state["recitation_input"]

                st.rerun()

        else:

            st.success("🎉 You memorized the entire line!")

            st.session_state.completed = True

    else:

        st.error("Not quite. Try again.")

        if result["mistakes"]:

            st.write("Mistakes:")

            for mistake in result["mistakes"]:

                mistake_type = mistake["type"]
                expected = mistake["expected"]
                heard = mistake["heard"]

                if mistake_type == "missing":

                    st.write(
                        f"Missing word: **{expected}**"
                    )

                elif mistake_type == "extra":

                    st.write(
                        f"Extra word: **{heard}**"
                    )

                elif mistake_type == "wrong_word":

                    st.write(
                        f"You said **{heard}**, "
                        f"but the expected word was "
                        f"**{expected}**."
                    )

                elif mistake_type == "wrong_order":

                    st.write(
                        f"Word order issue involving "
                        f"**{heard}** / **{expected}**."
                    )

        if st.button("Try Again"):

            st.session_state.submitted = False
            st.session_state.result = None
            st.session_state.phase = "reveal"
            st.session_state.reveal_start = time.time()

            if "recitation_input" in st.session_state:
                del st.session_state["recitation_input"]

            st.rerun()

# # -------------------------
# # Memorization exercise
# # -------------------------

# if st.session_state.get("started", False):

#     chunks = st.session_state.chunks

#     # Start with the last chunk
#     current_index = len(chunks) - 1
#     current_chunk = chunks[current_index]

#     # Record when the chunk was first displayed
#     if st.session_state.reveal_start is None:
#         st.session_state.reveal_start = time.time()

#     elapsed = time.time() - st.session_state.reveal_start

#     # Show chunk for five seconds
#     if elapsed < 5:

#         remaining = 5 - int(elapsed)

#         st.subheader("Memorize this:")

#         st.markdown(
#             f"### {current_chunk}"
#         )

#         st.write(f"Starting in {remaining}...")

#         time.sleep(0.1)
#         st.rerun()

#     # After five seconds, hide chunk and allow user to type it
#     else:

#         st.subheader("Your turn")

#         st.write(
#             "Type the chunk you just memorized:"
#         )

#         response = st.text_input(
#             "Recite the chunk",
#             key="recitation_input"
#         )

#         if st.button("Check Answer"):

#             if not response.strip():

#                 st.warning("Please enter your response.")

#             else:

#                 with st.spinner("Checking your answer..."):

#                     result = evaluate_recitation(
#                         current_chunk,
#                         response
#                     )

#                 st.session_state.result = result
#                 st.session_state.submitted = True

#                 st.rerun()


# # -------------------------
# # Results
# # -------------------------

# if st.session_state.get("submitted", False):

#     result = st.session_state.result

#     if result["correct"]:

#         st.success("Correct! 🎉")

#     else:

#         st.error("Not quite. Try again.")

#         if result["mistakes"]:

#             st.write("Mistakes:")

#             for mistake in result["mistakes"]:

#                 mistake_type = mistake["type"]
#                 expected = mistake["expected"]
#                 heard = mistake["heard"]

#                 if mistake_type == "missing":

#                     st.write(
#                         f"Missing word: **{expected}**"
#                     )

#                 elif mistake_type == "extra":

#                     st.write(
#                         f"Extra word: **{heard}**"
#                     )

#                 elif mistake_type == "wrong_word":

#                     st.write(
#                         f"You said **{heard}**, "
#                         f"but the expected word was **{expected}**."
#                     )

#                 elif mistake_type == "wrong_order":

#                     st.write(
#                         f"Word order issue involving "
#                         f"**{heard}** / **{expected}**."
#                     )

#         if st.button("Try Again"):

#             st.session_state.submitted = False
#             st.session_state.result = None
#             st.session_state.reveal_start = time.time()

#             if "recitation_input" in st.session_state:
#                 del st.session_state["recitation_input"]

#             st.rerun()