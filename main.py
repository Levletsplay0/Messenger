from fastapi import FastAPI
from database import init_db
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from pathlib import Path as FilePath
from routers import auth, users, groups, ws

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    FilePath("static").mkdir(parents=True, exist_ok=True)
    
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(ws.router)

@app.get("/")
async def main():
    return {"success": True, "message": "Прекрасно, бекенд работает!"}

app.mount("/static", StaticFiles(directory="static"), name="static")