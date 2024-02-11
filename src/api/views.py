from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy import func
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

    if url_instance is None:
        raise HTTPException(status_code=404, detail="Shortened URL not found")

    # Создаем запись в таблице `Log`
    log_entry = Log(
        url_id=url_instance.id,
        client_info=request.client.host,  # пример получения информации о клиенте
    )
    db.add(log_entry)
    await db.commit()

    # Перенаправляем на оригинальный URL
    return RedirectResponse(url=url_instance.original_url, status_code=307)


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
