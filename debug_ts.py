import requests
from bs4 import BeautifulSoup

html = requests.get("https://thingspeak.mathworks.com/channels/public?page=1").text
soup = BeautifulSoup(html, 'html.parser')
channel_tiles = soup.find_all('div', class_='channel-tile')
if channel_tiles:
    print("Found channel-tile classes")
else:
    channel_tiles = soup.find_all('div', class_='panel')
    print(f"Found {len(channel_tiles)} 'panel' classes")
    if channel_tiles:
        print(channel_tiles[0].prettify())
