
import os
import google.generativeai as genai
import json

def list_models():
    # Load config to get API key
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('gemini_settings', {}).get('api_key')
            if not api_key:
                print("No API key found in config.json")
                return
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)

    print("\nListing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
