import requests
import json

url = "https://rapidapi.com/gateway/graphql"
query = """
query searchApis($searchApiWhereInput: SearchApiWhereInput!, $paginationInput: PaginationInput, $searchApiOrderByInput: SearchApiOrderByInput) {
  products: searchApis(
    where: $searchApiWhereInput
    pagination: $paginationInput
    orderBy: $searchApiOrderByInput
  ) {
    nodes {
      id
      name
      description
      categoryName
    }
    pageInfo {
      endCursor
      hasNextPage
    }
    total
  }
}
"""

variables = {
    "paginationInput": {
        "first": 5,
        "after": ""
    },
    "searchApiOrderByInput": {
        "sortingFields": [
            {
                "fieldName": "ByRelevance",
                "by": "ASC"
            }
        ]
    },
    "searchApiWhereInput": {
        "term": "iot",
        "tags": []
    }
}

payload = {
    "operationName": "searchApis",
    "variables": variables,
    "query": query
}

headers = {
    "Content-Type": "application/json",
    "rapid-client": "hub-service",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

r = requests.post(url, json=payload, headers=headers)
print("Status:", r.status_code)
print("Response:", r.text[:1000])
