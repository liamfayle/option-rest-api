from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.controllers import stocks
from app.utils.success_return_format import success_return

router = APIRouter()

@router.get("/tickers")
async def get_tickers(
    apiKey: str = Query(None, title="Client API Key")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required."})
    
    ticker_data = await stocks.get_tickers(apiKey)
    return success_return(ticker_data)


@router.get("/ticker-info")
async def get_ticker_info(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Ticker to get info for")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})

    ticker_data = await stocks.get_ticker_info(apiKey, ticker)
    return success_return(ticker_data)


@router.get("/hist/price")
async def get_ticker_info(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Ticker to get info for"),
    start: str = Query(None, title="Start date for price data"),
    end: str = Query(None, title="End date for price data")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})

    ticker_data = await stocks.get_hist_price(apiKey, ticker, start, end)
    return success_return(ticker_data)


@router.get("/hist/splits")
async def get_hist_splits(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Ticker to get info for")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})

    ticker_data = await stocks.get_hist_splits(apiKey, ticker)
    return success_return(ticker_data)



@router.get("/hist/divs")
async def get_hist_divs(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Ticker to get info for")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})

    ticker_data = await stocks.get_hist_divs(apiKey, ticker)
    return success_return(ticker_data)



@router.get("/hist/earnings")
async def get_hist_earnings(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Ticker to get info for")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})

    ticker_data = await stocks.get_hist_earnings(apiKey, ticker)
    return success_return(ticker_data)