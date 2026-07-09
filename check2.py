import asyncio, os, sys
sys.path.insert(0, r'C:\Users\starw\ghost_engine_temporal')

async def check():
    from temporalio.client import Client
    API_KEY = None
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    if b"TEMPORAL_API_KEY=" in line and not line.strip().startswith(b"#"):
                        API_KEY = line.split(b"=", 1)[1].strip().decode()
                        break
        if API_KEY:
            break

    client = await Client.connect(
        "ap-northeast-1.aws.api.temporal.io:7233",
        namespace="quickstart-derekjami-878d5147.kydxq",
        api_key=API_KEY, tls=True,
    )

    wid = "ghost-engine-campaign-3ffe053e"
    handle = client.get_workflow_handle(wid)
    events = [e async for e in handle.fetch_history_events()]
    print(f"Total events: {len(events)}")
    types = {}
    for e in events:
        t = str(e.event_type)
        types.setdefault(t, []).append(e.event_id)
    for t, ids in types.items():
        print(f"  {t}: {ids[:5]}{'...' if len(ids)>5 else ''}")

asyncio.run(check())
