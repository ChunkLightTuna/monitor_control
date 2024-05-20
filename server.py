import json
import logging

from fastapi import HTTPException, Request, FastAPI, status, APIRouter
from fastapi.responses import FileResponse, HTMLResponse, Response

from lcd import Message
from menu import Menu

router = APIRouter()

with open('index.html', 'r') as f:
    index = HTMLResponse(content=f.read())

favicon = FileResponse(path='favicon.ico', media_type="text/x-favicon")


@router.get("/favicon.ico")
async def get_favicon():
    return favicon


@router.get("/")
async def get_index():
    return index


@router.post("/")
async def post(request: Request):
    body = await request.body()

    try:
        line_one, line_two = json.loads(body.decode('utf-8'))
        if not line_one and not line_two:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both lines empty")
        elif len(line_one) > 16 or len(line_two) > 16:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max 16 char per line")
        else:
            message = Message(line_one, line_two)
            menu: Menu | None = request.app.extra.get('menu')
            if menu:
                await menu.tmp_mode(message)
            else:
                logging.info(message)

            return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        if 'not enough values to unpack' in repr(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya gotta give me something")
        else:
            logging.error(repr(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


if __name__ == '__main__':
    import sys
    import uvicorn

    app = FastAPI()
    app.include_router(router)
    port = int(sys.argv[-1]) if len(sys.argv) > 1 else 8080
    uvicorn.run(app, host='0.0.0.0', port=port)
