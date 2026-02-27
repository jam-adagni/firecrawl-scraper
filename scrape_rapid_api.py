import requests
import json
import time

def scrape_rapid():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "rapid-client": "hub-service"
    }
    
    # 1. Get CSRF token
    csrf_url = "https://rapidapi.com/gateway/csrf"
    r_csrf = session.get(csrf_url, headers=headers)
    print("CSRF Response:", r_csrf.status_code)
    try:
        csrf_data = r_csrf.json()
        csrf_token = csrf_data.get('csrfToken')
        print("Obtained CSRF Token:", csrf_token)
    except:
        print("Failed to get CSRF from JSON, trying headers")
        csrf_token = r_csrf.headers.get('csrf-token')

    if not csrf_token:
        print("No CSRF token found.")
        return

    # 2. GraphQL Search
    graphql_url = "https://rapidapi.com/gateway/graphql"
    query = """
    query searchApis($searchApiWhereInput: SearchApiWhereInput!, $paginationInput: PaginationInput, $searchApiOrderByInput: SearchApiOrderByInput) {
      products: searchApis(
        where: $searchApiWhereInput
        pagination: $paginationInput
        orderBy: $searchApiOrderByInput
      ) {
        nodes {
          name
          description
          categoryName
          id
        }
        pageInfo {
          endCursor
          hasNextPage
        }
        total
      }
    }
    """
    
    all_apis = []
    cursor = ""
    terms = ["iot", "cloud", "data", "sensor", "api"]
    
    for term in terms:
        if len(all_apis) >= 1000: break
        print(f"Searching for term: {term}")
        cursor = ""
        for _ in range(10): # up to 10 pages per term
            variables = {
                "paginationInput": {"first": 100, "after": cursor},
                "searchApiOrderByInput": {"sortingFields": [{"fieldName": "ByRelevance", "by": "ASC"}]},
                "searchApiWhereInput": {"term": term, "tags": []}
            }
            payload = {
                "operationName": "searchApis",
                "variables": variables,
                "query": query
            }
            headers["csrf-token"] = csrf_token
            
            r = session.post(graphql_url, json=payload, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if not data.get('data') or not data['data'].get('products'):
                    print(f"No results for {term} at cursor {cursor}")
                    break
                
                nodes = data['data']['products']['nodes']
                all_apis.extend(nodes)
                print(f"Collected {len(all_apis)} items so far.")
                
                page_info = data['data']['products']['pageInfo']
                if not page_info.get('hasNextPage'):
                    break
                cursor = page_info['endCursor']
            else:
                print(f"Error {r.status_code}: {r.text}")
                break
            
            if len(all_apis) >= 1200: break
            time.sleep(1)

    # 3. Save to file
    with open('rapid_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_apis, f, indent=2)
    print(f"Saved {len(all_apis)} items to rapid_data.json")

if __name__ == "__main__":
    scrape_rapid()
