import re
import json

def parse_ipros(markdown):
    rows = []
    # Pattern to find ### [Title](link) and then the next immediately following - Company: [Company Name](link)
    # Using re.DOTALL to match across newlines between heading and company
    product_blocks = re.split(r'###\s+\[', markdown)
    for block in product_blocks[1:]:
        title_match = re.match(r'([^\]]+)\]\((https://mono\.ipros\.com/en/product/detail/[^)]+)\)', block)
        if not title_match:
            continue
        title = title_match.group(1).strip()
        link = title_match.group(2).strip()
        
        # Extract description (the text right after the heading until the Company line)
        desc_match = re.search(r'\)\n+(.*?)\n+\-\s+Company：', block, re.DOTALL)
        desc = desc_match.group(1).strip() if desc_match else ""
        desc = re.sub(r'[*_]', '', desc) # clean bold/italics
        desc = re.sub(r'\s+', ' ', desc).strip()
        desc = desc[:500]
        
        company_match = re.search(r'\-\s+Company：\s*\[([^\]]+)\]', block)
        company = company_match.group(1).strip() if company_match else "mono.ipros.com"
        
        # Sometimes title contains image artifacts or brackets
        title = re.sub(r'\[.*?\]\s*', '', title).strip() # remove [Beginner's Edition] etc. if needed, or just leave it
        
        rows.append({
            "dataset_name": title,
            "source": company,
            "description": desc,
            "updated_date": "",
            "data_format": ""
        })
    return rows

if __name__ == "__main__":
    with open('ipros_markdown.txt', 'r', encoding='utf-8') as f:
        md = f.read()
    print(json.dumps(parse_ipros(md), indent=2))
