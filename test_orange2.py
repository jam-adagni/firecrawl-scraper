import re
import json

def parse_orange(markdown):
    rows = []
    links = re.findall(r'\[([^\]]+)\]\((https?://iotjourney\.orange\.com/en/catalogue/[^)]+)\)', markdown)
    seen = set()
    for name, link in links:
        name = name.strip()
        if name.lower() in ("i am looking for", "devices", "technology", "data and device management", "orange connected validation", "view the entire catalogue", "catalogue"):
            continue
        # Remove any bold/italic syntax and 'image' text if it leaked
        name = re.sub(r'[*_]', '', name).strip()
        name = re.sub(r'\s+image$', '', name, flags=re.IGNORECASE).strip()
        if len(name) < 3: continue
        
        if name.lower() not in seen:
            seen.add(name.lower())
            rows.append({
                "dataset_name": name,
                "source": link,
                "description": "Orange IoT Journey Catalogue Category",
                "updated_date": "",
                "data_format": ""
            })
    return rows

if __name__ == "__main__":
    with open('orange_markdown.txt', 'r', encoding='utf-8') as f:
        md = f.read()
    print(json.dumps(parse_orange(md), indent=2))
