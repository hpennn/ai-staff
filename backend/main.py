import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import chat, staff, webhook, auth, admin, subscription

# Initialize database
init_db()

app = FastAPI(title="AI客服员工系统", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes - auth is public
app.include_router(auth.router, prefix="/api")
# Chat and webhook are public
app.include_router(chat.router, prefix="/api")
app.include_router(webhook.router, prefix="/api")
# Staff routes (some public, some require auth internally)
app.include_router(staff.router, prefix="/api")
# Admin routes (all require auth)
app.include_router(admin.router, prefix="/api")
app.include_router(subscription.router, prefix="/api")

# Static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(os.path.join(frontend_path, "manifest.json"))


@app.get("/sw.js")
async def serve_sw():
    return FileResponse(os.path.join(frontend_path, "sw.js"))


@app.get("/icons/{filename}")
async def serve_icon(filename: str):
    return FileResponse(os.path.join(frontend_path, "icons", filename))


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "AI客服员工系统运行中"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
