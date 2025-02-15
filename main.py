import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from multiprocessing import Process

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from bot import dp, bot, router
from config import Config
from database import JSONDatabase
import uvicorn

db = JSONDatabase('redirects.json')

ERROR_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirect Not Found</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-white p-8 rounded-lg shadow-xl max-w-md w-full text-center">
        <h1 class="text-4xl font-bold text-gray-800 mb-4">404</h1>
        <p class="text-xl text-gray-600 mb-6">Oops! This redirect doesn't exist.</p>
        <div class="space-y-4">
            <a href="javascript:history.back()" 
               class="block w-full py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600 transition duration-200">
                Go Back
            </a>
            <a href="https://t.me/your_bot" 
               class="block w-full py-2 px-4 bg-gray-500 text-white rounded hover:bg-gray-600 transition duration-200">
                Create Your Redirect
            </a>
        </div>
    </div>
</body>
</html>
"""


class SubdomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        host = request.headers.get('host', '')

        if host == Config.DOMAIN:
            return RedirectResponse(url=Config.MAIN_REDIRECT)

        subdomain = host.split('.')[0]

        await db.cleanup_expired()

        redirect = await db.get_redirect(subdomain)
        if not redirect:
            redirect = await db.get_temp_redirect(subdomain)

        if not redirect:
            return HTMLResponse(content=ERROR_PAGE, status_code=404)

        request_info = {
            "referrer": request.headers.get("referer", "direct"),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "country": request.headers.get("cf-ipcountry", "unknown"),
            "ip": request.client.host,
            "timestamp": datetime.now().isoformat(),
            "duration": time.time() - start_time
        }

        asyncio.create_task(db.update_stats(subdomain, request_info))

        target_url = redirect['url']
        path = request.url.path

        if path and path != '/':
            if '/IGNORE' in path:
                path = path.split('/IGNORE')[0]
            target_url = f"{target_url.rstrip('/')}{path}"

        return RedirectResponse(url=target_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.cleanup_expired()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SubdomainMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/stats/{subdomain}")
async def get_stats(subdomain: str, request: Request):
    # Простая защита API через header
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != Config.API_KEY:
        return {"error": "Unauthorized"}, 401

    redirect = await db.get_redirect(subdomain)
    if not redirect:
        redirect = await db.get_temp_redirect(subdomain)

    if not redirect:
        return {"error": "Redirect not found"}, 404

    return {
        "subdomain": subdomain,
        "url": redirect["url"],
        "stats": redirect.get("stats", {})
    }


async def run_bot():
    dp.include_router(router)
    await dp.start_polling(bot)


def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_bot_process():
    asyncio.run(run_bot())

if __name__ == "__main__":
    bot_process = Process(target=run_bot_process)
    api_process = Process(target=run_api)

    bot_process.start()
    api_process.start()

    try:
        bot_process.join()
        api_process.join()
    except KeyboardInterrupt:
        print("Shutting down...")
        bot_process.terminate()
        api_process.terminate()
        bot_process.join()
        api_process.join()
