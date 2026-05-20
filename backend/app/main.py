from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()
frontend_origin = settings.frontend_origin.rstrip("/")
parsed_frontend = urlparse(frontend_origin)
frontend_origins = {frontend_origin}
if parsed_frontend.scheme and parsed_frontend.port:
    frontend_origins.add(f"{parsed_frontend.scheme}://127.0.0.1:{parsed_frontend.port}")
    frontend_origins.add(f"{parsed_frontend.scheme}://localhost:{parsed_frontend.port}")

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)
app.mount("/static", StaticFiles(directory=settings.object_storage_dir), name="static")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
