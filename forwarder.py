import asyncio
import httpx
from fastapi import Request, Response
from starlette.responses import JSONResponse
import logging
logging.basicConfig(level=logging.INFO)

import config
from key_manager import key_manager

async def forward_request(request: Request):
    auth_key = request.headers.get("x-goog-api-key") or request.query_params.get("key")

    if not auth_key or (auth_key != config.AUTH_KEY and auth_key not in config.GEMINI_API_KEYS):
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    gemini_key = await key_manager.get_next_key()
    if not gemini_key:
        return JSONResponse(status_code=503, content={"error": "All keys are currently exhausted"})

    client = httpx.AsyncClient()
    url = httpx.URL(config.UPSTREAM_URL).join(request.url.path.lstrip('/'))
    if config.DEBUG:
        logging.info(f"Forwarding request to URL: {url}")
    
    query_params = dict(request.query_params)
    if "key" in query_params:
        del query_params["key"]
    query_params["key"] = gemini_key

    headers = dict(request.headers)
    headers["host"] = httpx.URL(config.UPSTREAM_URL).host

    for _ in range(config.MAX_RETRIES + 1 if config.MAX_RETRIES > 0 else 1_000_000):
        try:
            response = await client.request(
                method=request.method,
                url=url,
                params=query_params,
                headers=headers,
                content=await request.body(),
            )

            if response.status_code != 503:
                if response.status_code == 429:
                    error_data = response.json()
                    quota_id = error_data.get("error", {}).get("details", [{}]).get("metadata", {}).get("quotaId")
                    if quota_id:
                        await key_manager.handle_resource_exhausted(gemini_key, quota_id)
                response_content = response.content
                if config.DEBUG:
                    logging.info(f"Response: {response.status_code} {response_content}")
                return Response(content=response_content, status_code=response.status_code, headers=response.headers)

        except httpx.RequestError as e:
            return JSONResponse(status_code=500, content={"error": f"Request failed: {e}"})
        
        await asyncio.sleep(config.RETRY_DELAY_SECONDS)

    return JSONResponse(status_code=503, content={"error": "Model overloaded, all retries failed"})