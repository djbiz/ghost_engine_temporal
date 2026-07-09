import asyncio, os, sys
sys.path.insert(0, r'C:\Users\starw\ghost_engine_temporal')

async def check():
    from temporalio.client import Client
    API_KEY = None
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    if b"TEMPORAL_API_KEY=" in line and not line.strip().endswith(b"#"):
                        API_KEY = line.split(b"=", 1)[1].strip().decode()
                        break
        if API_KEY:
            break

    client = await Client.connect(
        "ap-northeast-1.aws.api.temporal.io:7233",
        namespace="quickstart-derekjami-878d5147.kydxq",
        api_key=API_KEY, tls=True,
    )

    for wid in ["ghost-engine-campaign-3ffe053e"]:
        handle = client.get_workflow_handle(wid)
        desc = await handle.describe()
        events = [e async for e in handle.fetch_history_events()]
        act_scheduled = [e.event_id for e in events if str(e.event_type) == "EventType.ACTIVITY_TASK_SCHEDULED"]
        act_completed = [e.event_id for e in events if str(e.event_type) == "EventType.ACTIVITY_TASK_COMPLETED"]
        print(f"\n=== {wid} ===")
        print(f"Status: {desc.status} | Events: {len(events)} | Activities: scheduled={len(act_scheduled)}, completed={len(act_completed)}")
        print(f"Start: {desc.start_time} | Close: {desc.close_time}")

asyncio.run(check())
