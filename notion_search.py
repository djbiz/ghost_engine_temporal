import json, subprocess, os

# Read NOTION_API_KEY from .env
env_path = r"C:\Users\starw\AppData\Local\hermes\.env"
notion_key = None
with open(env_path) as f:
    for line in f:
        if line.startswith("NOTION_API_KEY="):
            notion_key = line.strip().split("=", 1)[1]
            break

print(f"Key found: {notion_key[:10]}..." if notion_key else "Key NOT found")

# Search for MiroFish pages
cmd = [
    "curl", "-s", "-X", "POST", "https://api.notion.com/v1/search",
    "-H", f"Authorization: Bearer {notion_key}",
    "-H", "Notion-Version: 2025-09-03",
    "-H", "Content-Type: application/json",
    "-d", '{"query": "MiroFish", "filter": {"value": "page", "property": "object"}}'
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
print(f"Curl exit: {result.returncode}")
print(f"STDOUT: {result.stdout[:500]}")
print(f"STDERR: {result.stderr[:200]}")
