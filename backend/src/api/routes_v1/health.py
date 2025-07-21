from litestar import get
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK



@get("/health", tags=["System"])
async def health_check() -> Response:
    return Response(content={"status": "ok"}, status_code=HTTP_200_OK)



