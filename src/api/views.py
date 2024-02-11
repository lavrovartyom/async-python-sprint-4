from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import func
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from db import get_session
from models import URL, Log
from services.function import some_short_id_generation_function

router = APIRouter()


class UrlCreate(BaseModel):
    url: HttpUrl


class UrlResponse(BaseModel):
    short_id: str


@router.get(path="/ping")
async def ping_database(db: AsyncSession = Depends(get_session)):
    try:
        result = await db.execute(select(func.now()))

        return JSONResponse(
            content={"status": "available", "time": str(result.scalar())},
            status_code=200,
        )
    except OperationalError as op_err:
        return JSONResponse(
            content={
                "status": "unavailable",
                "error": "OperationalError",
                "detail": str(op_err),
            },
            status_code=503,
        )
    except DBAPIError as dbapi_err:
        return JSONResponse(
            content={
                "status": "unavailable",
                "error": "DBAPIError",
                "detail": str(dbapi_err),
            },
            status_code=503,
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unavailable",
                "error": "UnknownError",
                "detail": str(e),
            },
            status_code=503,
        )


@router.post(path="/", response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    url_create: UrlCreate, db: AsyncSession = Depends(get_session)
):
    db_url = await db.execute(select(URL).where(URL.original_url == url_create.url))
    db_url = db_url.scalars().first()
    if db_url:
        return {"short_id": db_url.short_id}

    new_url = URL(original_url=url_create.url)
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)

    new_url.short_id = some_short_id_generation_function(new_url.id)
    await db.commit()

    return {"url": new_url.original_url, "short_id": new_url.short_id}


@router.get("/{short_id}")
async def redirect_to_original(
    short_id: str, request: Request, db: AsyncSession = Depends(get_session)
):
    result = await db.execute(select(URL).where(URL.short_id == short_id))
    url_instance = result.scalars().first()

    if url_instance is None or not url_instance.is_active:
        raise HTTPException(
            status_code=410 if not url_instance.is_active else 404,
            detail="URL not found or deleted",
        )

    log_entry = Log(
        url_id=url_instance.id,
        client_info=request.client.host,
    )
    db.add(log_entry)
    await db.commit()

    return RedirectResponse(url=url_instance.original_url, status_code=307)


@router.delete("/{short_id}", status_code=status.HTTP_200_OK)
async def delete_url(short_id: str, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(URL).where(URL.short_id == short_id))
    url_instance = result.scalars().first()

    if url_instance is None:
        raise HTTPException(status_code=404, detail="URL not found")

    url_instance.is_active = False
    await db.commit()

    return {"detail": "URL deleted successfully."}


@router.get("/{short_id}/status")
async def get_url_usage(
    short_id: str,
    full_info: Optional[bool] = False,
    max_result: Optional[int] = 10,
    offset: Optional[int] = 0,
    db: AsyncSession = Depends(get_session),
):
    url_instance = await db.execute(select(URL).where(URL.short_id == short_id))
    url_instance = url_instance.scalars().first()

    if url_instance is None:
        raise HTTPException(status_code=404, detail="Shortened URL not found")

    logs_query = select(Log).where(Log.url_id == url_instance.id)

    if full_info:
        logs = await db.execute(
            logs_query.order_by(Log.accessed_at.desc()).limit(max_result).offset(offset)
        )
        logs = logs.scalars().all()

        return {
            "total": await db.execute(
                select(func.count(Log.id)).where(Log.url_id == url_instance.id)
            ),
            "logs": [
                {"accessed_at": log.accessed_at, "client_info": log.client_info}
                for log in logs
            ],
        }

    total = await db.execute(
        select(func.count(Log.id)).where(Log.url_id == url_instance.id)
    )
    total = total.scalar()

    return {"total": total}
