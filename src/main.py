import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api import views
from core import config
from db import dispose_db, init_db

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

app.include_router(views.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await dispose_db()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.PROJECT_HOST,
        port=config.PROJECT_PORT,
    )
