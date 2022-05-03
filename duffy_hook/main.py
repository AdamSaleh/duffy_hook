from typing import Optional

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}



@app.api_route("/echo", methods=["GET", "POST", "DELETE"])
async def test(request):
    json = await request.json()
    return {"method": request.method, "body": json}

