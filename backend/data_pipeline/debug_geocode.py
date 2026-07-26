"""
Standalone diagnostic — run this alone to see exactly what Nominatim
returns, including HTTP status and raw response body.

    python debug_geocode.py
"""
import requests

URL = "https://nominatim.openstreetmap.org/search"
UA = "taoyuan-ltc-navigator/0.1 (contact: replace-with-your-email@example.com)"

test_queries = [
    "桃園市八德區, Taiwan",
    "Taipei 101, Taiwan",
    "桃園市八德區樹仁三街601號, Taiwan",
]

for q in test_queries:
    print(f"\n--- Query: {q} ---")
    try:
        resp = requests.get(
            URL,
            params={"q": q, "format": "json", "limit": 1, "countrycodes": "tw"},
            headers={"User-Agent": UA},
            timeout=10,
        )
        print("Status code:", resp.status_code)
        print("Response headers Content-Type:", resp.headers.get("Content-Type"))
        print("Raw body (first 500 chars):", resp.text[:500])
    except Exception as e:
        print("Request exception:", repr(e))
