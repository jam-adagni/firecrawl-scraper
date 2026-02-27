import requests
import json

url = "https://www.wi-fi.org/product-finder"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

print("Fetching from", url)
try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Status code:", response.status_code)
    with open('wifi_raw.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Saved wifi_raw.html")
except Exception as e:
    print("Error:", e)
