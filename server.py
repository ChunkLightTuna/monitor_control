import json
import logging

import uvicorn
from fastapi import HTTPException, Request, FastAPI, status
from fastapi.responses import FileResponse, HTMLResponse, Response

from lcd import Messageable

app = FastAPI()
with open('index.html', 'r') as f:
    index = HTMLResponse(content=f.read())

favicon = FileResponse(path='favicon.ico', media_type="text/x-favicon")


@app.get("/favicon.ico")
async def get_favicon():
    return favicon


@app.get("/")
async def get_index():
    return index


@app.post("/")
async def post(request: Request):
    body = await request.body()
    try:
        line_one, line_two = json.loads(body.decode('utf-8'))
        if not line_one and not line_two:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both lines empty")
        elif len(line_one) > 16 or len(line_two) > 16:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max 16 char per line")
        else:
            app.state.lcd.msg(line_one, line_two)
            return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        if 'not enough values to unpack' in repr(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya gotta give me something")
        else:
            logging.error(repr(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def run(messageable: Messageable, port=1602):
    app.state.lcd = messageable
    uvicorn.run(app, port=port)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()


    class Stub(Messageable):
        def msg(self, line_one: str, line_two: str = None):
            logging.debug(f'\n<<{line_one}>>\n<<{line_two}>>')


    run(Stub())
