import httpx
import asyncio
import xmltodict
from fastapi import Depends
from pydantic import BaseModel
from typing import Dict, Any
from models import Dronespot as DronespotModel, Place as PlaceModel

from sqlalchemy.orm import Session

from core.config import settings
import json

from database.mariadb_session import get_db, SessionLocal


class APIRequestParams(BaseModel):
    numOfRows: int
    pageNo: int
    MobileOS: str
    MobileApp: str
    mapX: float
    mapY: float
    radius: int
    contentTypeId: int
    serviceKey: str


data_store: Dict[str, Any] = {}


async def fetch_page(params: APIRequestParams) -> Dict[str, Any]:
    url = (
        "https://apis.data.go.kr/B551011/KorService1/locationBasedList1"
        f"?numOfRows={params.numOfRows}"
        f"&pageNo={params.pageNo}"
        f"&MobileOS={params.MobileOS}"
        f"&MobileApp={params.MobileApp}"
        f"&mapX={params.mapX}"
        f"&mapY={params.mapY}"
        f"&radius={params.radius}"
        f"&contentTypeId={params.contentTypeId}"
        f"&serviceKey={params.serviceKey}"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            xml_content = response.text

            parsed_data = xmltodict.parse(xml_content)

            return parsed_data

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error occurred: {e}"}
    except httpx.RequestError as e:
        return {"error": f"Request error occurred: {e}"}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}


async def getplace(mapX: float, mapY: float) -> Dict[int, Any]:
    params = APIRequestParams(
        numOfRows=200,
        pageNo=1,
        MobileOS="ETC",
        MobileApp="Dravel",
        mapX=mapX,
        mapY=mapY,
        radius=20000,
        contentTypeId=39,
        serviceKey=settings.TOURAPI_LDM_KEY
    )

    all_data = []
    page_limit = 1
    while params.pageNo <= page_limit:
        data = await fetch_page(params)

        if 'error' in data:
            return {"message": "Failed to fetch data", "data": data}


        response = data.get('response', {})
        body = response.get('body', {})

        total_count = int(body.get('totalCount', 0))
        items = body.get('items', {}).get('item', [])


        all_data.extend(items)
        params.pageNo += 1

        page_limit = (total_count + params.numOfRows - 1) // params.numOfRows

    extracted_data = {}
    index = 0
    for item in all_data:
        title = item.get('title')
        if title:
            index += 1
            extracted_data[index] = {
                'title': item.get('title'),
                'addr1': item.get('addr1'),
                'contentid': item.get('contentid'),
                'contenttypeid': item.get('contenttypeid'),
                'mapx': item.get('mapx'),
                'mapy': item.get('mapy')
            }

    return extracted_data


async def main():
    db: Session = SessionLocal()
    try:
        spot_id = 10
        spot_db = db.query(DronespotModel).filter(DronespotModel.id == spot_id).first()
        if not spot_db:
            print("Spot not found")
            return

        mapX = spot_db.lon
        mapY = spot_db.lat
        result = await getplace(mapX, mapY)  # 비동기 함수 호출
        for index in range(1, len(result)):
            place_data = PlaceModel(
                name=result[index]['title'],
                type=result[index]['contentid'],
                lat=result[index]['mapy'],
                lon=result[index]['mapx'],
                address=result[index]['addr1'],
                place_type_id=result[index]['contenttypeid']
            )
            db.add(place_data)
            db.commit()
            db.refresh(place_data)

        print("완료")
    finally:
        db.close()  # 세션을 명시적으로 종료


if __name__ == "__main__":
    asyncio.run(main())
