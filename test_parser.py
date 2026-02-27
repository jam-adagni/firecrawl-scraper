import re

def extract_rows(markdown):
    rows = []
    blocks = re.findall(r'\n\d{2}\. (.*?)(?=\n\d{2}\. |\nShare|\Z)', '\n' + markdown, re.DOTALL)
    for block in blocks:
        block = block.strip()
        if not block: continue
        title_match = re.search(r'#\s+(.+)', block)
        if not title_match: continue
        title = title_match.group(1).strip()
        
        sources = re.findall(r'^-\s+(.+)$', block, re.MULTILINE)
        sources = [s.strip() for s in sources]
        source_str = ", ".join(sources)
        
        updated_match = re.search(r'Updated\s+([A-Za-z]+\s+\d+,?\s+\d{4})', block)
        updated_date = updated_match.group(1).strip() if updated_match else ""
        
        format_match = re.search(r'^(zip|pcap|csv|pdf|excel|ppt|pdf,excel,csv,ppt)$', block, re.MULTILINE | re.IGNORECASE)
        data_format = format_match.group(1).strip() if format_match else ""
        
        rows.append({
            "dataset_name": title,
            "source": source_str,
            "updated_date": updated_date,
            "data_format": data_format
        })
    return rows

with open('markdown.txt', 'r', encoding='utf-8') as f:
    text = f.read()

res = extract_rows(text)
import json
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
