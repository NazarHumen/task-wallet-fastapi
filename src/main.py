from fastapi import FastAPI

from src.auth.router import router as auth_router
from fastapi.responses import RedirectResponse
app = FastAPI(title="TaskWallet")

@app.get("/")
def root():
    return RedirectResponse(url="/docs")
app.include_router(auth_router)
