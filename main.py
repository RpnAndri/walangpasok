from fastapi import FastAPI
from tools import wp_checker
from datetime import datetime

app = FastAPI()

@app.get("/walang-pasok/{date}")
async def walang_pasok(date: str):

    return await wp_checker(str(date))