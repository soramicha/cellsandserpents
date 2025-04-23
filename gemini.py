from google import genai
import os # to access env var
from dotenv import load_dotenv, find_dotenv

# load env file
_ = load_dotenv(find_dotenv())
key = os.environ.get('GEMINI_API_KEY')

client = genai.Client(api_key=key)

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="tell me about a fairy dying in a small paragraph"
)

print(response.text)