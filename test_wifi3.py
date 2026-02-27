import sys
import requests
import json

r = requests.get('http://prf.cert.wi-fi.org/products/view/filtered', params={'sort_by':'default', 'sort_order':'desc', 'page':1})
data = r.json()
# let's look at the first item
item = data['items'][0]
print("Item keys:", item.keys())
print("Company:", item.get('company', {}).get('name'))
print("Product:", item.get('name'))
print("Product URL id:", item.get('cid'))
print("Description:", item.get('description', ''))
print("Categories:", [c.get('name') for c in item.get('categories', [])])
print("Date:", item.get('date'))
print("Total items from pagination:", data.get('pagination', {}).get('total_items'))
