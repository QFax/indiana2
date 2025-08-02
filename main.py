from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
import uvicorn

import config
from forwarder import forward_request
from key_manager import key_manager

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get(config.REPORTING_PATH)
async def status_report():
    return key_manager.get_status()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request):
    return await forward_request(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)