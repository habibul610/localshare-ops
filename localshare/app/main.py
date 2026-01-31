
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import APP_NAME
from .database import engine, Base, get_db
from .models import User
from .auth import router as auth_router, get_current_user
from .files import router as files_router
from .messages import router as messages_router
from .websocket import manager
from .cleanup import cleanup_expired_files

# Create tables
Base.metadata.create_all(bind=engine)

# Background task wrapper
async def periodic_cleanup():
    while True:
        # Run cleanup every minute
        cleanup_expired_files()
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run cleanup once and start loop
    print("Initial cleanup...")
    cleanup_expired_files()
    task = asyncio.create_task(periodic_cleanup())
    yield
    # Shutdown
    task.cancel()

app = FastAPI(title=APP_NAME, lifespan=lifespan)

# Mount Static
app.mount("/static", StaticFiles(directory="localshare/static"), name="static")

# Templates
templates = Jinja2Templates(directory="localshare/templates")

# Routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(files_router, tags=["Files"])
app.include_router(messages_router, tags=["Messages"])
from .websocket import router as ws_router
app.include_router(ws_router, tags=["WebSocket"])

# Web UI Routes

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Check if logged in. If not, login. If yes, app.
    # We can't easily check cookie valid here without dependency which might raise HTTPException.
    # We check manually.
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/app")
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "app_name": APP_NAME})

@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request, current_user: User = Depends(get_current_user)):
    # Render the main SPA shell
    return templates.TemplateResponse("app.html", {
            "request": request, 
            "app_name": APP_NAME, 
            "user": current_user
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("localshare.app.main:app", host="0.0.0.0", port=8000, reload=True)
