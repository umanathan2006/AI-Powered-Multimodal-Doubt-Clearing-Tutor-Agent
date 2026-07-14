from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="OS Tutor Backend")

# All actual endpoints live in api/routes.py, not here.
# main.py's only job is to create the app and plug routers into it.
app.include_router(router)
