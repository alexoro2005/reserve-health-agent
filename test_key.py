"""Quick check that your Claude API key works. Run: python test_key.py"""
from dotenv import load_dotenv
import anthropic

load_dotenv(".env")
client = anthropic.Anthropic()
try:
    models = [m.id for m in client.models.list(limit=10)]
    print("SUCCESS - your key works.")
    print("Models you can use:", ", ".join(models[:6]))
except anthropic.AuthenticationError:
    print("The key was rejected. Make a new one under Console -> API Keys and paste it into .env")
except Exception as e:
    print("Couldn't reach the API:", type(e).__name__, e)
