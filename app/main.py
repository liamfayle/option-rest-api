from fastapi import FastAPI
from app.routers import stocks, options
from app.config.db_config import market_db
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware


app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

#EXCEPTIONS / ERROR CODES
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "data": {}}
    )



#STARTUP / SHUTDOWN EVENTS

@app.on_event("startup")
async def startup():
    await market_db.connect()

@app.on_event("shutdown")
async def shutdown():
    await market_db.disconnect()



#ROUTES
    
app.include_router(stocks.router, prefix="/stocks")
app.include_router(options.router, prefix="/options")