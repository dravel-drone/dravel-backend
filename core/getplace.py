import httpx
import asyncio
import xmltodict
from pydantic import BaseModel
from typing import Dict, Any
from core.config import settings
import json


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


async def getplace(mapX: float, mapY: float) -> Dict[str, Any]:
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
    for item in all_data:
        title = item.get('title')
        if title:
            extracted_data[title] = {
                'addr1': item.get('addr1'),
                'contentid': item.get('contentid'),
                'contenttypeid': item.get('contenttypeid'),
                'mapx': item.get('mapx'),
                'mapy': item.get('mapy')
            }

    return extracted_data


async def main():
    mapX = 126.575834
    mapY = 33.427337
    result = await getplace(mapX, mapY)
    #print(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
