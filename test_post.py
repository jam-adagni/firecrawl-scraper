import requests

url = "http://prf.cert.wi-fi.org/products/view/filtered"

for page in [1, 2]:
    # Test as POST data
    payload = {
        "page": page,
        "sort_by": "default",
        "sort_order": "desc"
    }
    r = requests.post(url, data=payload)
    data = r.json()
    items = data.get("items", [])
    if items:
        print(f"Page {page} first item cid: {items[0].get('cid')}")
    else:
        print(f"Page {page} empty")
