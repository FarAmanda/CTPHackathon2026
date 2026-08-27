import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

print("1. Loading environment...", flush=True)
load_dotenv(override=True)

print("2. Initializing client...", flush=True)
client = genai.Client()

print("3. Requesting Gemini API (15s timeout)...", flush=True)
try:
    interaction = client.interactions.create(
        model="gemini-3.7-flash",
        input="Explain how AI works in a few words",
        )
    
    print("\n4. Output received:")
    print(interaction.output_text)


except Exception as e:
    print(f"\n❌ Request failed: {e}", flush=True)