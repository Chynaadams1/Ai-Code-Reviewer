from fastapi import FastAPI
from api.routes_github import router as github_router

app = FastAPI()

@app.get("/status")
async def status():
    return {"status": "ok"}

app.include_router(github_router)
