import urllib.request, json

key = "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"
page_id = "391dbc2b-713e-8155-805e-fabde075cf8d"

# Read as markdown
url = f"https://api.notion.com/v1/pages/{page_id}/markdown"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        md = data.get("markdown", "")
        print("Title:", data.get("title", ""))
        print("Content length:", len(md))
        print("Preview:", md[:1000])
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode()[:300])
