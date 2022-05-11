from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi import Header
from fastapi import Request
app = FastAPI()


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
            pass
    else:
        try:
            payload = await request.json()
            print(payload)
        except Exception as e:
            print("Couldn't get payload:", e)

        return {"message": "Unable to process action"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
