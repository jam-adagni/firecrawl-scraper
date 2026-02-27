import requests
import json

r = requests.get('http://prf.cert.wi-fi.org/products/view/filtered', params={'sort_by':'default', 'sort_order':'desc'}).json()
diff = {k: v for k, v in r.items() if k != 'items'}
with open('wifi_root.json','w') as f:
    f.write(json.dumps(diff, indent=2))
