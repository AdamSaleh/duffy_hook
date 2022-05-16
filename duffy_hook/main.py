import os
from typing import Optional

import uvicorn
from cicoclient import CicoWrapper
from fastapi import FastAPI
from fastapi import Header
from fastapi import Request

app = FastAPI()

api = CicoWrapper(
            endpoint="http://admin.ci.centos.org:8080/",
            api_key=os.environ.get("CICO_API_KEY"),
)


@app.get('/')
def read_root():
    return {'Hello': 'World'}


@app.get('/items/{item_id}')
def read_item(item_id: int, q: Optional[str] = None):
    return {'item_id': item_id, 'q': q}


@app.post("/webhook/{app_name}")
async def receive_payload(
    request: Request,
    app_name: str,
    x_github_event: str = Header(...),
):
    print("event:", x_github_event)

    if x_github_event == "ping":
        return {"message": "pong"}
    if x_github_event == "workflow_job":
        payload = await request.json()
        labels = payload['workflow_job']['labels']
        if 'stream-8' in labels:
            print("Request with labels:", labels)
#            hosts, ssid = api.node_get(
#                arch="x86_64",
#                ver="8-stream",
#                count=1,
#                retry_count=2,
#                retry_interval=30)
# {'n63.pufty': {'host_id': 127, 'hostname': 'n63.pufty',
# 'ip_address': '172.19.3.127', 'chassis': 'pufty',
# 'used_count': 4411, 'current_state': 'Deployed',
# 'comment': '6f76948a', 'distro': None, 'rel': None,
# 'centos_version': '8-stream', 'architecture': 'x86_64',
# 'node_pool': 1, 'console_port': 2620, 'flavor': None}}
    else:
        try:
            payload = await request.json()
            print(payload)
        except Exception as e:
            print("Couldn't get payload:", e)

        return {"message": "Unable to process action"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
