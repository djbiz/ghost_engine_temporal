import urllib.request, json, urllib.error

key = "ntn_58...GcJ7"
page_id = "391dbc2b-713e-8155-805e-fabde075cf8d"

# Test: create a new page under page_id 3
url = "https://api.notion.com/v1/pages"
payload = json.dumps({
    "parent": {"page_id": page_id},
    "properties": {"title": {"title": [{"text": {"content": "Test Page"}}]}}
}).encode()
req = urllib.request.Request(url, data=payload, headers={"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("CREATE OK:", resp.status, resp.read().decode()[:100])
except urllib.error.HTTPError as e:
    print("CREATE Error:", e.code, e.read().decode()[:300])

# Test: append divider to page 3
url2 = f"https://api.notion.com/v1/blocks/{page_id}/children"
payload2 = json.dumps({"children": [{"object": "block", "type": "divider", "divider": {}}]}).encode()
req2 = urllib.request.Request(url2, data=payload2, headers={"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}, method="PATCH")
try:
    with urllib.request.urlopen(req2, timeout=15) as resp:
        print("APPEND OK:", resp.status)
except urllib.error.HTTPError as e:
    print("APPEND Error:", e.code, e.read().decode()[:300])
