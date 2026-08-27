import streamlit as st
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from a .env file (if present)
load_dotenv()

st.set_page_config(page_title="Costar - Actor Sorting Assistant", page_icon="🎭")
st.title("🎭 Costar - Actor Sorting Assistant")

# Initialize the Gemini client
# Automatically reads GEMINI_API_KEY from environment or .env file
client = genai.Client()

# Casting assistant system instructions
SYSTEM_PROMPT = """
You are an expert casting director assistant for the Costar-Actors app.
Help users evaluate, filter, and sort actors based on audition criteria, 
character breakdowns, union status, age ranges, and role requirements.
"""

# Initialize conversation history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I can help you sort and match actors for your production. What role or criteria are you looking for?"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input prompt
if prompt := st.chat_input("Describe the role or paste actor criteria..."):
    # Add and render user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response via Gemini
    with st.chat_message("assistant"):
        with st.spinner("Analyzing criteria..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config={"system_instruction": SYSTEM_PROMPT}
                )
                assistant_reply = response.text
                st.markdown(assistant_reply)
            except Exception as e:
                assistant_reply = f"Error: {e}"
                st.error(assistant_reply)

    # Save response to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})