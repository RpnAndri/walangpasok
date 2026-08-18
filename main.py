from fastapi import FastAPI
from tools.wp_checker import wp_checker

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)

@app.get( "/", response_class=HTMLResponse,)
async def index(
    request: Request,
):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/api/walang-pasok")
async def walang_pasok(
    date: str | None = None,
):
    if date is None:
        from datetime import date as dt_date

        date = dt_date.today().isoformat()

    return await wp_checker(date)