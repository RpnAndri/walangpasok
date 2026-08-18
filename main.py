from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from tools.wp_checker import wp_checker


app = FastAPI(
    title="Suspended Ba",
)

BASE_DIR = Path(__file__).resolve().parent

GEOJSON_FILE = (
    BASE_DIR
    / "data"
    / "philippines.geojson"
)

NCR_GEOJSON_FILE = (
    BASE_DIR
    / "data"
    / "ncr.geojson"
)


TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)

app.mount(
    "/data",
    StaticFiles(
        directory=BASE_DIR / "data"
    ),
    name="data",
)

@app.get(
    "/",
    response_class=HTMLResponse,
)
async def index(
    request: Request,
):
    return templates.TemplateResponse(
    request=request,
    name="index.html",
)


@app.get("/api/suspensions")
async def get_suspensions(
    date_: str | None = None,
):
    """
    Return class suspension information.

    Example:

    /api/suspensions?date_=2026-08-14
    """

    if date_ is None:
        date_ = date.today().isoformat()

    return await wp_checker(date_)

# @app.get("/api/geojson")
# async def get_geojson():

#     return FileResponse(
#         NCR_GEOJSON_FILE,
#         media_type="application/geo+json",
#     )