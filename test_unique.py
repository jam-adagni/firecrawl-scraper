import requests

ids = set()
for page_num in range(1, 12):
    url = "http://prf.cert.wi-fi.org/products/view/filtered"
    params = {"sort_by": "default", "sort_order": "desc", "page": page_num}
    r = requests.get(url, params=params).json()
    for item in r.get("items", []):
        ids.add(item.get("id"))

print("Fetched 11 pages, total items loop:", 11*10)
print("Unique IDs fetched:", len(ids))
