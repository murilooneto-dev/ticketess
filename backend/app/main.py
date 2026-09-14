import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.api.dashboard import router as dashboard_router
from app.api.github import router as github_router
from app.api.projects import router as projects_router
from app.api.project_ideas import router as project_ideas_router
from app.api.reports import router as reports_router
from app.api.system import router as system_router
from app.api.tickets import router as tickets_router
from app.config import settings
from app.scheduler.scheduler import shutdown_scheduler, start_scheduler
from app.security.middleware import SecurityHeadersMiddleware
from app.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

for directory in (
    settings.data_dir,
    settings.storage_dir,
    settings.reports_dir,
    settings.backups_dir,
    settings.logs_dir,
):
    directory.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    logger.info("%s started (env=%s)", settings.APP_NAME, settings.APP_ENV)
    yield
    shutdown_scheduler()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(system_router)
app.include_router(projects_router)
app.include_router(project_ideas_router)
app.include_router(tickets_router)
app.include_router(github_router)
app.include_router(dashboard_router)
app.include_router(reports_router)

frontend_dist = settings.frontend_dist_dir
if frontend_dist.is_dir():
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # index.html e arquivos soltos (ex.: logo.png) não têm hash no nome,
        # então nunca devem ser cacheados agressivamente pelo navegador —
        # só os arquivos dentro de /assets (com hash) podem.
        no_cache_headers = {"Cache-Control": "no-cache"}
        candidate = frontend_dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate, headers=no_cache_headers)
        return FileResponse(frontend_dist / "index.html", headers=no_cache_headers)
else:
    logger.warning("Frontend build not found at %s. Run 'npm run build' in frontend/.", frontend_dist)
