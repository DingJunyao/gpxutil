from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.gpxutil.utils.db_connect import AreaCodeConnectHandler
from src.gpxutil.utils.gdf_handler import GDFListHandler
from src.gpxutil_server.router import route, gpx
from src.gpxutil_server.core.db import init_mongodb, init_mongodb_sync
from src.gpxutil_server.router import task


@asynccontextmanager
async def lifespan(app: FastAPI):
    GDFListHandler()
    AreaCodeConnectHandler()
    init_mongodb_sync()
    await init_mongodb()
    yield
app = FastAPI(lifespan=lifespan)
app.include_router(gpx.router)
app.include_router(route.router)
app.include_router(task.router)




if __name__ == '__main__':
    import uvicorn
    uvicorn.run('src.gpxutil_server.main:app', host="0.0.0.0", port=8000, reload=True)