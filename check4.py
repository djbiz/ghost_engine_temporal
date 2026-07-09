import asyncio, os, sys
sys.path.insert(0, r'C:\Users\starw\ghost_engine_temporal')

async def check():
    from temporalio.client import Client
    API_KEY = None
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    if b"APOLLO_API_KEY" in line and not line.strip().startswith(b"#"):
                        key = line.split(b"=", 1)[1].strip().decode()
                        if key:
                            API_KEY = key
                            break
        if API_KEY:
            break

    print(f"APOLLO_API_KEY found: {API_KEY is not None}, starts with: {API_KEY[:8] if API_KEY else None}...")

    for wid in ["ghost-engine-campaign-c65ca0e6", "ghost-engine-campaign-3ffe053e"]:
        try:
            from temporalio.client import Client
            API_KEY_TEMP = None
            for path in [r"C:\Users\starw\AppData\Local\hermes\.env"]:
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        for line in f:
                            if b"TEMPORAL_API_KEY" in line and not line.strip().startswith(b"#"):
                                key = line.split(b"=", 1)[1].strip().decode()
                                if key:
                                    API_KEY_TEMP = key
                                    break
                        if API_KEY_TEMP:
                            break
            client = Client.connect(
                "ap-northeast-1.aws.api.temporal.io:7233",
                namespace="quickstart-derekjami-878d5147.kydxq",
                api_key=API_KEY_TEMP, tls=True,
            )
            h = client.get_workflow_handle(wid)
            d = await h.describe()
            events = [ev async for ev in h.fetch_history_events()]
            print(f"\n=== {wid} ===")
            print(f"Status: {d.status} | Events: {len(events)}")
            print(f"Start: {d.start_time} | Close: {d.close_time}")
            # Show activity details
            for ev in events:
                if ev.event_id in [2, 3, 4, 5, 6, 7]:
                    attrs = getattr(ev, 'activity_task_scheduled_event_attributes', None)
                    if attrs:
                        print(f"  Event {ev.event_id}: ACTIVITY_SCHEDULED - {attrs.activity_type.name if hasattr(attrs, 'activity_type') else attrs}")
        except Exception as ex:
            print(f"{wid}: {ex}")

    # Test Apollo API directly
    if API_KEY:
        import requests
        print(f"\n--- Testing Apollo API ---")
        print(f"Key: {API_KEY[:8]}...")
        resp = requests.get(
            "https://api.apollo.io/v1/contacts/search",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"page": 1, "per_page": 1},
            timeout=10,
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Contacts found: {data.get('total_entries', 'N/A')}")
        else:
            print(f"Error: {resp.text[:300]}")
    else:
        print("\nNo APOLLO_API_KEY found in .env")

asyncio.run(check())
