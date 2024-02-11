import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api import views
from core.config import settings
from db import dispose_db, init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

app.include_router(views.router)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await dispose_db()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.PROJECT_HOST,
        port=settings.PROJECT_PORT,
    )
