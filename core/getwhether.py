import json

import httpx

from pydantic import BaseModel
from models import (
    Whether
)
from sqlalchemy.orm import Session
from database.mariadb_session import SessionLocal

from datetime import datetime, timedelta
from typing import (
    Union,
    Dict,
    Tuple,
    Any
)
from core.config import settings


class APIRequestParams(BaseModel):
    serviceKey: str
    nx: int
    ny: int
    base_date: str
    base_time: str
    dataType: str


def is_whether_valid(db: Session, dronespot_id: int) -> Tuple[bool, Union[None, Whether]]:
    data = db.query(Whether).filter(Whether.dronespot_id == dronespot_id).first()
    if data is None:
        return False, None

    now = datetime.utcnow() + timedelta(hours=9)

    created_at = data.created_at
    time_difference = now - created_at

    if time_difference >= timedelta(hours=3):
        return False, data
    return True, data


def get_latest_time():
    now = datetime.utcnow() + timedelta(hours=9)

    times = [
        now.replace(hour=2, minute=15, second=0, microsecond=0),
        now.replace(hour=5, minute=15, second=0, microsecond=0),
        now.replace(hour=8, minute=15, second=0, microsecond=0),
        now.replace(hour=11, minute=15, second=0, microsecond=0),
        now.replace(hour=14, minute=15, second=0, microsecond=0),
        now.replace(hour=17, minute=15, second=0, microsecond=0),
        now.replace(hour=20, minute=15, second=0, microsecond=0),
        now.replace(hour=23, minute=15, second=0, microsecond=0)
    ]

    past_times = [t for t in times if t <= now]

    if not past_times:
        return times[-1] - timedelta(days=1)

    return max(past_times)


async def fetch_whether(params: APIRequestParams) -> Any:
    url = (
        "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        f"?serviceKey={params.serviceKey}"
        f"&nx={params.nx}"
        f"&ny={params.ny}"
        f"&base_date={params.base_date}"
        f"&base_time={params.base_time}"
        f"&dataType={params.dataType}"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code != 200:
                print(response.status_code, response.text)
                return None
            data = response.text
            return json.loads(data)
    except Exception as e:
        return None


async def get_whether_data(
    dronespot_id: int,
    nx: int,
    ny: int,
):
    db: Session = SessionLocal()

    valid_data = is_whether_valid(db, dronespot_id)
    whether_data = valid_data[1]
    if not valid_data[0]:
        broadcast_time = get_latest_time()
        response_data = await fetch_whether(
            APIRequestParams(
                serviceKey=settings.WHETHER_API_KEY,
                nx=nx,
                ny=ny,
                base_date=broadcast_time.strftime('%Y%m%d'),
                base_time=broadcast_time.strftime('%H0000'),
                dataType='json'
            )
        )

        if response_data is None:
            return None

        if whether_data is not None:
            db.delete(whether_data)

        temp = sky = pty = None
        for data in response_data['response']['body']['items']['item']:
            if data['category'] == 'TMP':
                temp = int(float(data['fcstValue']))
            elif data['category'] == 'SKY':
                sky = int(data['fcstValue'])
            elif data['category'] == 'PTY':
                pty = int(data['fcstValue'])

        if temp is None or sky is None or pty is None:
            return None

        new_whether_data = Whether(
            dronespot_id=dronespot_id,
            created_at=broadcast_time,
            sky=sky,
            pty=pty,
            degree=temp
        )
        db.add(new_whether_data)
        db.commit()
        whether_data = new_whether_data
    return {
        'tmp': whether_data.degree,
        'sky': whether_data.sky,
        'pty': whether_data.pty
    }
