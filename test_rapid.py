import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('FIRECRAWL_API_KEY')

url = "https://rapidapi.com/search/iot"

headers = {"Authorization": f"Bearer {API_KEY}"}
payload = {
    "url": url,
    "formats": ["markdown"]
}

print(f"Requesting {url} via Firecrawl...")
response = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=payload)

if response.status_code == 200:
    data = response.json()
    markdown = data.get('data', {}).get('markdown', '')
    with open('rapid_markdown.txt', 'w', encoding='utf-8') as f:
        f.write(markdown)
    print("Markdown saved to rapid_markdown.txt")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
