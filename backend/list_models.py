import os, google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print('API key set:', bool(api_key))
if not api_key:
    raise SystemExit('No API key')
genai.configure(api_key=api_key)
models = genai.list_models()
print('Available models:')
for m in models:
    print(m.name)
