import asyncio, os, sys
sys.path.insert(0, r'C:\Users\starw\ghost_engine_temporal')

async def check():
    from temporalio.client import Client
    API_KEY = None
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    if b"TEMPORAL_API_KEY" in line and not line.strip().startswith(b"#"):
                        key = line.split(b"=", 1)[1].strip().decode()
                        if key:
                            API_KEY = key
                            break
        if API_KEY:
            break

    client = await Client.connect(
        "ap-northeast-1.aws.api.temporal.io:7233",
        namespace="quickstart-derekjami-878d5147.kydxq",
        api_key=API_KEY, tls=True,
    )

    for wid in ["ghost-engine-campaign-c65ca0e6", "ghost-engine-campaign-3ffe053e"]:
        try:
            h = client.get_workflow_handle(wid)
            d = await h.describe()
            events = [ev async for ev in h.fetch_history_events()]
            print(f"{wid}: status={d.status}, events={len(events)}, start={d.start_time}, close={d.close_time}")
        except Exception as ex:
            print(f"{wid}: {ex}")

asyncio.run(check())
