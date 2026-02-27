import re

markdown = """# Search Engine for the Internet of Everything

## Shodan is the world's first search engine for Internet-connected devices. Discover how Internet intelligence can help you make better decisions.

[Sign Up Now](https://www.shodan.io/dashboard)

![Map of the Internet](https://www.shodan.io/static/img/pingmap-955f4777.png)

###### Explore the Platform

# _Beyond_ the Web

Websites are just one part of the Internet. Use Shodan to discover everything from power plants, mobile phones, refrigerators and Minecraft servers.

# _Monitor_ Network Exposure

Keep track of all your devices that are directly accessible from the Internet. Shodan provides a comprehensive view of all exposed services to help you stay secure.

# Internet _Intelligence_

Learn more about who is using various products and how they're changing over time. Shodan gives you a data-driven view of the technology that powers the Internet."""

def extract_shodan(md):
    rows = []
    # Match # Heading followed by text, until next # or end
    sections = re.findall(r'^#\s+(.+?)\n+(.*?)(?=\n#|\Z)', md, re.MULTILINE | re.DOTALL)
    for title, desc in sections:
        # Clean title from markdown (like _Beyond_)
        clean_title = re.sub(r'[_*]', '', title).strip()
        # Clean description (remove extra newlines, limited length)
        clean_desc = re.sub(r'\s+', ' ', desc).strip()
        rows.append({
            "dataset_name": clean_title,
            "source": "shodan.io",
            "description": clean_desc[:500]
        })
    return rows

if __name__ == "__main__":
    import json
    print(json.dumps(extract_shodan(markdown), indent=2))
