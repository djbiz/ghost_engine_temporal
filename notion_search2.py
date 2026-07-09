import json, urllib.request, urllib.error, os

env_path = r"C:\Users\starw\AppData\Local\hermes\.env"
notion_key = None
with open(env_path) as f:
    for line in f:
        if "NOTION_API_KEY" in line and "=" in line:
            notion_key = line.strip().split("=", 1)[1]
            break

print(f"Key: {notion_key[:10]}..." if notion_key else "NOT FOUND")

url = "https://api.notion.com/v1/search"
payload = json.dumps({"query": "MiroFish", "filter": {"value": "page", "property": "object"}}).encode()
req = urllib.request.Request(
    url, data=payload,
    headers={
        "Authorization": f"Bearer {notion_key}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json"
    },
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        results = data.get("results", [])
        print(f"Status: {resp.status}")
        print(f"Results: {len(results)}")
        for r in results:
            print(f"  {r['id']} | {r.get('url','')}")
except urllib.error.HTTPError as e:
    print(f"HTTPError {e.code}: {e.read().decode()[:300]}")
except Exception as ex:
    print(f"Error: {ex}")
