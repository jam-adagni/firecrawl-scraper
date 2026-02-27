import requests
import json

url = "https://www.wi-fi.org/products/view/filtered?companies=122" # intel
# wait, the API is http://prf.cert.wi-fi.org/products/view/filtered ?
url2 = "http://prf.cert.wi-fi.org/api/products/view/filtered" # I will just try a few

for test_url in [
    "http://prf.cert.wi-fi.org/products/view/filtered",
    "https://api.wi-fi.org/products/view/filtered"
]:
    try:
        r = requests.get(test_url, params={"sort_by":"default", "sort_order":"desc", "page":1})
        print(test_url, r.status_code)
    except Exception as e:
        print(test_url, e)

# maybe grab the json from the HTML
with open('wifi_raw.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
m = re.search(r'"productFinder":(.*?\})},"ajaxTrustedUrl"', html)
if m:
    data = json.loads("{" + '"productFinder":' + m.group(1) + "}")
    print("Found productFinder keys:", data.get('productFinder', {}).keys())
    if 'products' in data['productFinder']:
        print("Total products in html:", data['productFinder']['products']['pagination']['total_items'])
        print("Sample product:", json.dumps(data['productFinder']['products']['items'][0], indent=2))
