from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.controllers import options
from app.utils.success_return_format import success_return
from app.utils.valid_number_check import is_valid_float, is_valid_int
import json
import gzip
from app.models.options import is_date_valid
import numpy as np

router = APIRouter()

DAY_TO_TRADING_DAY = 1.45


@router.get("/hist/expiries")
async def get_hist_expiries(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want expiries (yyyy-mm-dd)")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})
    
    ticker_data = await options.get_hist_expiries(apiKey, ticker, tradeDate)
    return success_return(ticker_data)


@router.get("/hist/strikes")
async def get_hist_strikes(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want strikes (yyyy-mm-dd)"),
    expiry: str = Query(None, title="Expiry on which you want strikes *optional* (yyyy-mm-dd)")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})
    
    ticker_data = await options.get_hist_strikes(apiKey, ticker, tradeDate, expiry)
    return success_return(ticker_data)



@router.get("/hist/price")
async def get_hist_price(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want prices (yyyy-mm-dd)"),
    expiry: str = Query(None, title="Expiry on which you want prices *optional* (yyyy-mm-dd)"),
    strike: str = Query(None, title="Strike on which you want prices *optional*"),
    type: str = Query(None, title="Type on which you want prices *optional*")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})

    if type is not None:
        type = type.upper() 

    if type is not None and type not in ['P', 'C']:
        return JSONResponse(status_code=400, content={"message": "Invalid type. Must be 'P' or 'C'.", 'data': {}})
    
    if strike is not None and not is_valid_float(strike):
        return JSONResponse(status_code=400, content={"message": "Invalid strike must be proper number format.", 'data': {}})
    
    ticker_data = await options.get_hist_price(apiKey, ticker, tradeDate, expiry, strike, type)
    return success_return(ticker_data)



@router.get("/hist/quotes")
async def get_hist_quotes(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want prices (yyyy-mm-dd)"),
    expiry: str = Query(None, title="Expiry on which you want prices *optional* (yyyy-mm-dd)"),
    strike: str = Query(None, title="Strike on which you want prices *optional*"),
    type: str = Query(None, title="Type on which you want prices *optional*")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})

    if type is not None:
        type = type.upper() 

    if type is not None and type not in ['P', 'C']:
        return JSONResponse(status_code=400, content={"message": "Invalid type. Must be 'P' or 'C'.", 'data': {}})
    
    if strike is not None and not is_valid_float(strike):
        return JSONResponse(status_code=400, content={"message": "Invalid strike must be proper number format.", 'data': {}})
    
    ticker_data = await options.get_hist_quotes(apiKey, ticker, tradeDate, expiry, strike, type)

    return success_return(ticker_data)



@router.get("/hist/iv-rank")
async def get_hist_ivrank(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want prices (yyyy-mm-dd)"),
    lookbackPeriod: str = Query(None, title="Period for calculation *optional*"),
    ivDTE: str = Query(None, title="Frequency of IV for calculation *optional*"),
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})
    
    #check lookback
    if lookbackPeriod is not None and not is_valid_int(lookbackPeriod):
        return JSONResponse(status_code=400, content={"message": "Invalid period must be integer format.", 'data': {}})
    
    if lookbackPeriod is not None:
        lookbackPeriod = int( np.ceil(int(lookbackPeriod) / DAY_TO_TRADING_DAY) )
    else:
        lookbackPeriod = 252

    if lookbackPeriod is not None and lookbackPeriod < 1:
        return JSONResponse(status_code=400, content={"message": "Period must be atleast 1.", 'data': {}})
    
    if lookbackPeriod is not None and lookbackPeriod > 730:
        return JSONResponse(status_code=400, content={"message": "Two years (730 days) is highest allowed lookback period.", 'data': {}})
    
    #check iv dte
    if ivDTE is not None and not is_valid_int(ivDTE):
        return JSONResponse(status_code=400, content={"message": "Invalid ivDTE must be integer format.", 'data': {}})
    
    if ivDTE is not None:
        ivDTE = int(ivDTE)
    else:
        ivDTE = 30

    if ivDTE < 1:
        return JSONResponse(status_code=400, content={"message": "Period must be atleast 1 day.", 'data': {}})
    
    if ivDTE > 365:
        return JSONResponse(status_code=400, content={"message": "1 year (365 days) is highest allowed ivDTE period.", 'data': {}})
    
    
    ticker_data = await options.get_hist_ivrank(apiKey, ticker, tradeDate, lookbackPeriod, ivDTE)
    return success_return(ticker_data)



@router.get("/hist/vol-cone")
async def get_hist_volcone(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want prices (yyyy-mm-dd)"),
    lookbackPeriod: str = Query(None, title="Period for calculation *optional*"),
    dte: str = Query(None, title="DTE for part of vol cone")
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})
    
    #check lookback
    if lookbackPeriod is not None and not is_valid_int(lookbackPeriod):
        return JSONResponse(status_code=400, content={"message": "Invalid period must be integer format.", 'data': {}})
    
    if lookbackPeriod is not None:
        lookbackPeriod = int( np.ceil(int(lookbackPeriod) / DAY_TO_TRADING_DAY) )
    else:
        lookbackPeriod = 504

    if lookbackPeriod is not None and lookbackPeriod < 1:
        return JSONResponse(status_code=400, content={"message": "Period must be atleast 1 day.", 'data': {}})
    
    #check iv dte
    if dte is not None and not is_valid_int(dte):
        return JSONResponse(status_code=400, content={"message": "Invalid ivDTE must be integer format.", 'data': {}})
    
    if dte is not None:
        dte = int(dte)
    else:
        dte = 30

    if dte < 1:
        return JSONResponse(status_code=400, content={"message": "Period must be atleast 1.", 'data': {}})
    
    if dte > 365:
        return JSONResponse(status_code=400, content={"message": "1 year (365) is highest allowed dte period.", 'data': {}})
    
    
    ticker_data = await options.get_hist_volcone(apiKey, ticker, tradeDate, lookbackPeriod, dte)
    return success_return(ticker_data)




@router.get("/hist/earnings")
async def get_hist_earnings(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want prices (yyyy-mm-dd)"),
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})
    
    ticker_data = await options.get_hist_earnings(apiKey, ticker, tradeDate)
    return success_return(ticker_data)



@router.get("/hist/iv-info")
async def get_hist_ivinfo(
    apiKey: str = Query(None, title="Client API Key"),
    ticker: str = Query(None, title="Stock ticker to search"),
    tradeDate: str = Query(None, title="Trade date on which you want prices (yyyy-mm-dd)"),
    expiry: str = Query(None, title="Expiry on which you want prices *optional* (yyyy-mm-dd)"),
):
    if apiKey is None:
        return JSONResponse(status_code=400, content={"message": "API key is required.", "data": {}})
    
    if ticker is None:
        return JSONResponse(status_code=400, content={"message": "Ticker is required.", "data": {}})
    
    if tradeDate is None:
        return JSONResponse(status_code=400, content={"message": "Trade Date is required.", "data": {}})

    if not await is_date_valid(tradeDate):
        return JSONResponse(status_code=400, content={"message": "Trade date does not exist", "data": {}})
    
    ticker_data = await options.get_hist_ivinfo(apiKey, ticker, tradeDate, expiry)
    return success_return(ticker_data)