import httpx
import asyncio
import xmltodict
from fastapi import Depends
from pydantic import BaseModel
from typing import Dict, Any

from models import Dronespot as DronespotModel, Place as PlaceModel, DronePlace as DronePlaceModel
from sqlalchemy.orm import Session
from core.config import settings
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


class APIRequestParamsImg(BaseModel):
    MobileOS: str
    MobileApp: str
    contentId: str
    imageYN: str
    subImageYN: str
    numOfRows: int
    pageNo: int
    serviceKey: str


def is_place_exists(db: Session, content_id: str) -> bool:
    return db.query(PlaceModel).filter(PlaceModel.type == content_id).first() is not None


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


async def getplace(mapX: float, mapY: float, contentTypeId: int) -> Dict[int, Any]:
    params = APIRequestParams(
        numOfRows=200,
        pageNo=1,
        MobileOS="ETC",
        MobileApp="Dravel",
        mapX=mapX,
        mapY=mapY,
        radius=20000,
        contentTypeId=contentTypeId,
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


async def fetch_page_imag(params: APIRequestParamsImg) -> Dict[str, Any]:
    url = (
        "https://apis.data.go.kr/B551011/KorService1/detailImage1"
        f"?MobileOS={params.MobileOS}"
        f"&MobileApp={params.MobileApp}"
        f"&contentId={params.contentId}"
        f"&imageYN={params.imageYN}"
        f"&subImageYN={params.subImageYN}"
        f"&numOfRows={params.numOfRows}"
        f"&pageNo={params.pageNo}"
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


async def getplace_img(contentId: str) -> Dict[int, Any]:
    params = APIRequestParamsImg(
        numOfRows=200,
        pageNo=1,
        MobileOS="ETC",
        MobileApp="Dravel",
        imageYN="Y",
        subImageYN="Y",
        contentId=contentId,
        serviceKey=settings.TOURAPI_LDM_KEY
    )

    all_data = []

    # 이건 모든 페이지에 있는 사진 url 가져오는 코드
    # page_limit = 1
    # while params.pageNo <= page_limit:
    #     data = await fetch_page_imag(params)
    #     print("data", data)
    #
    #     if 'error' in data:
    #         return {"message": "Failed to fetch data", "data": data}
    #
    #     response = data.get('response', {})
    #     body = response.get('body', {})
    #
    #     total_count = int(body.get('totalCount', 0))
    #     if total_count > 0:
    #         items = body.get('items', {}).get('item', [])
    #         # `items`가 딕셔너리인 경우 리스트로 변환
    #         if isinstance(items, dict):
    #             items = [items]
    #         if items is not None:
    #             all_data.extend(items)
    #     else:
    #         all_data.append(None)
    #     params.pageNo += 1
    #     page_limit = (total_count + params.numOfRows - 1) // params.numOfRows

    data = await fetch_page_imag(params)
    #print("data", data)

    if 'error' in data:
        return {"message": "Failed to fetch data", "data": data}

    response = data.get('response', {})
    body = response.get('body', {})

    total_count = int(body.get('totalCount', 0))
    if total_count > 0:
        items = body.get('items', {}).get('item', [])
        # `items`가 딕셔너리인 경우 리스트로 변환
        if isinstance(items, dict):
            items = [items]
        if items is not None:
            all_data.extend(items)
    else:
        all_data.append(None)

    extracted_data = {}
    index = 0
    for item in all_data:
        if item is None:
            index += 1
            extracted_data[index] = {
                'contentid': "None",
                'originimgurl': "None",
                'imgname': "None",
                'smallimageurl': "None",
                'cpyrhtDivCd': "None",
                'serialnum': "None"
            }
            continue
        contentid = item.get('contentid')
        #print("193번째 라인", contentid)
        if contentid:
            index += 1
            extracted_data[index] = {
                'contentid': item.get('contentid'),
                'originimgurl': item.get('originimgurl'),
                'imgname': item.get('imgname'),
                'smallimageurl': item.get('smallimageurl'),
                'cpyrhtDivCd': item.get('cpyrhtDivCd'),
                'serialnum': item.get('serialnum')
            }
    #print("extracted_data:", extracted_data)
    return extracted_data


async def save_place(spot_id: int):
    db: Session = SessionLocal()
    try:
        spot = db.query(DronespotModel).filter(DronespotModel.id == spot_id).first()

        # # 이미 이 드론스팟에 대한 장소가 저장되어 있는지 확인
        # existing_places = db.query(DronePlaceModel).filter(DronePlaceModel.dronespot_id == spot_id).first()
        # if existing_places:
        #     print(f"DroneSpot ID {spot_id}: 이미 장소가 저장되어 있습니다.")
        # else:
        #     # for spot in spot_list:
        #     #     spot_id = spot.id
        #     #
        #     #     # 이미 이 드론스팟에 대한 장소가 저장되어 있는지 확인
        #     #     existing_places = db.query(DronePlaceModel).filter(DronePlaceModel.dronespot_id == spot_id).first()
        #     #     if existing_places:
        #     #         print(f"DroneSpot ID {spot_id}: 이미 장소가 저장되어 있습니다. 건너뜁니다.")
        #     #         continue

        mapX = spot.lon
        mapY = spot.lat
        result_res = await getplace(mapX, mapY, 39)  # 비동기 함수 호출
        # print(result_res)
        result_accom = await getplace(mapX, mapY, 32)  # 비동기 함수 호출

        for index in range(1, len(result_res) + 1):
            content_id = result_res[index]['contentid']
            # print("식당:", content_id)

            # 이미 있는 장소 건너뛰기
            if is_place_exists(db, content_id):
                db_place = db.query(PlaceModel).filter(PlaceModel.type == content_id).first()
                db_droneplace = db.query(DronePlaceModel).filter(
                    DronePlaceModel.dronespot_id == spot_id,
                    DronePlaceModel.place_id == db_place.id
                ).first()
                if not db_droneplace:
                    drone_place_data = DronePlaceModel(
                        dronespot_id=spot_id,
                        place_id=db_place.id
                    )
                    # print(drone_place_data)
                    db.add(drone_place_data)
                    db.commit()
                continue

            image_res = await getplace_img(content_id)
            photo_url = "None"
            if image_res:
                photo_url = image_res[1]['originimgurl']
            place_data = PlaceModel(
                name=result_res[index]['title'],
                type=result_res[index]['contentid'],
                lat=result_res[index]['mapy'],
                lon=result_res[index]['mapx'],
                address=result_res[index]['addr1'],
                place_type_id=result_res[index]['contenttypeid'],
                photo_url=photo_url
            )

            db.add(place_data)
            db.commit()
            db.refresh(place_data)

            # drone_place 테이블에 추가
            drone_place_data = DronePlaceModel(
                dronespot_id=spot_id,
                place_id=place_data.id
            )

            db.add(drone_place_data)
            db.commit()

        for index in range(1, len(result_accom) + 1):
            content_id = result_accom[index]['contentid']
            # print("숙소:", content_id)

            # 이미 있는 장소 건너뛰기
            if is_place_exists(db, content_id):
                db_place = db.query(PlaceModel).filter(PlaceModel.type == content_id).first()
                db_droneplace = db.query(DronePlaceModel).filter(
                    DronePlaceModel.dronespot_id == spot_id,
                    DronePlaceModel.place_id == db_place.id
                ).first()
                if not db_droneplace:
                    drone_place_data = DronePlaceModel(
                        dronespot_id=spot_id,
                        place_id=db_place.id
                    )
                    # print(drone_place_data)
                    db.add(drone_place_data)
                    db.commit()
                continue

            image_accom = await getplace_img(content_id)
            photo_url = "None"
            if image_accom:
                photo_url = image_accom[1]['originimgurl']
            place_data = PlaceModel(
                name=result_accom[index]['title'],
                type=result_accom[index]['contentid'],
                lat=result_accom[index]['mapy'],
                lon=result_accom[index]['mapx'],
                address=result_accom[index]['addr1'],
                place_type_id=result_accom[index]['contenttypeid'],
                photo_url=photo_url
            )

            db.add(place_data)
            db.commit()
            db.refresh(place_data)

            # drone_place 테이블에 추가
            drone_place_data = DronePlaceModel(
                dronespot_id=spot_id,
                place_id=place_data.id
            )

            db.add(drone_place_data)
            db.commit()

        print(f"DroneSpot ID {spot_id}: 장소 저장 완료.")
    finally:
        db.close()

# if __name__ == "__main__":
#     asyncio.run(save_place(42))
