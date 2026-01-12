
import os
import google.generativeai as genai
from backend import llm_config

print(f"Checking models with API Key: {llm_config.GEMINI_API_KEY[:5]}...")

try:
    genai.configure(api_key=llm_config.GEMINI_API_KEY)
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
