import json
import re

def extract_ts(markdown):
    rows = []
    pattern = re.compile(r'\*\*([^*]+)\*\*\s*[\\]*\n[\s\\]*(.*?)\]\(([^)]+)\)', re.DOTALL)
    for m in pattern.finditer(markdown):
        title = m.group(1).strip()
        desc = m.group(2).strip()
        link = m.group(3).strip()
        domain_match = re.search(r'https?://([^/]+)/', link)
        source = domain_match.group(1) if domain_match else link
        rows.append({
            "dataset_name": title,
            "source": source,
            "description": desc,
            "updated_date": "",
            "data_format": ""
        })
    return rows

if __name__ == "__main__":
    with open('markdown_ts.txt', 'r', encoding='utf-8') as f:
        md = f.read()
    print(json.dumps(extract_ts(md), indent=2))
