import re
import json

def parse_datagov(markdown):
    rows = []
    blocks = re.split(r'###\s+\[', markdown)
    for block in blocks[1:]:
        title_match = re.match(r'([^\]]+)\]\((https?://catalog\.data\.gov/dataset/[^)]+)\)', block)
        if not title_match: continue
        title = title_match.group(1).strip()
        link = title_match.group(2).strip()
        
        # Match company and description
        # Company usually ends with " —"
        company_desc_match = re.search(r'\)\n+\s*(.+?)\s*—\n+\s*(.*?)\n+\s*\-', block, re.DOTALL)
        if company_desc_match:
            company = company_desc_match.group(1).strip()
            desc = company_desc_match.group(2).strip()
        else:
            # Fallback if no list of formats at the end
            company_desc_match = re.search(r'\)\n+\s*(.+?)\s*—\n+\s*(.*)', block, re.DOTALL)
            if company_desc_match:
                company = company_desc_match.group(1).strip()
                desc = company_desc_match.group(2).strip()
            else:
                company = "data.gov"
                desc = ""
        
        # clean desc
        desc = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        desc = desc[:500]
        
        # Match formats
        formats_match = re.findall(r'\-\s+\[(CSV|JSON|RDF|XML|GeoJSON|SHP|HTML|ZIP|TEXT)\]', block, re.IGNORECASE)
        data_format = ",".join(list(set(formats_match))) if formats_match else ""
        
        rows.append({
            "dataset_name": title,
            "source": company,
            "description": desc,
            "updated_date": "",
            "data_format": data_format
        })
    return rows

if __name__ == "__main__":
    with open('datagov_markdown.txt', 'r', encoding='utf-8') as f:
        md = f.read()
    res = parse_datagov(md)
    print(json.dumps(res, indent=2))
