import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('FIRECRAWL_API_KEY')
url = "https://catalog.data.gov/dataset?tags=iot"

headers = {"Authorization": f"Bearer {API_KEY}"}
payload = {
    "url": url,
    "pageOptions": {"onlyMainContent": False, "waitFor": 5000}
}
print("Fetching content...")
try:
    response = requests.post("https://api.firecrawl.dev/v0/scrape", json=payload, headers=headers)
    res_json = response.json()
    with open('datagov_response.json', 'w', encoding='utf-8') as f:
        json.dump(res_json, f)

    if "data" in res_json and "markdown" in res_json["data"]:
        with open('datagov_markdown.txt', 'w', encoding='utf-8') as f:
            f.write(res_json["data"]["markdown"])
        print("Markdown saved to datagov_markdown.txt")
    else:
        print("No markdown found.")
except Exception as e:
    print("Error:", e, response.text if response else "")
