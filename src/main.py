import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api import base
from core import config

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

app.include_router(base.router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.PROJECT_HOST,
        port=config.PROJECT_PORT,
    )
