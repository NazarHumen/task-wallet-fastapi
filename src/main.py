from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.admin_panel import setup_admin
from src.auth.router import router as auth_router
from src.db.database import engine
from src.tasks.router import router as tasks_router

app = FastAPI(title="TaskWallet")

# SQLAdmin
setup_admin(app, engine)


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


app.include_router(auth_router)
app.include_router(tasks_router)
