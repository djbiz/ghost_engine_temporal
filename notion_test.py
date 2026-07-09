import urllib.request, json

key = "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"
page_id = "391dbc2b-713e-8155-805e-fabde075cf8d"

# Test auth
url = "https://api.notion.com/v1/users/me"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        print("Auth OK:", str(data)[:200])
except urllib.error.HTTPError as e:
    print("Auth error:", e.code, e.read().decode()[:200])

# Read blocks
url2 = f"https://api.notion.com/v1/blocks/{page_id}/children"
req2 = urllib.request.Request(url2, headers={"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03"})
try:
    with urllib.request.urlopen(req2, timeout=15) as resp:
        data = json.loads(resp.read())
        print("Blocks:", len(data.get("results", [])))
except urllib.error.HTTPError as e:
    print("Blocks error:", e.code, e.read().decode()[:200])
