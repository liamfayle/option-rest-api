from app.models.stocks import *
from app.utils.api_key_check import check_api_key
from app.utils.date_check import is_valid_date
from fastapi import HTTPException


async def get_tickers(apiKey: str) -> list:
    '''
    Returns unique list of tickers

    :param apiKey: Client api key (string format)
    :return: list of tickers 
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    ticker_data = await get_tickers_db()

    return ticker_data


async def get_ticker_info(apiKey: str, ticker: str):
    '''
    Returns ticker info from stocks table

    :param apiKey: Client api key
    :param ticker: Ticker in str format (ie AAPL)
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    ticker = ticker.upper()
    ticker_data = await get_ticker_info_db(ticker)

    return ticker_data



async def get_hist_price(apiKey: str, ticker: str, start: str, end: str):
    '''
    Returns ticker info from stocks table

    :param apiKey: Client api key
    :param ticker: Ticker in str format (ie AAPL)
    :param start: (Optional) start date in yyyy-mm-dd format
    :param end: (Optional) end date in yyyy-mm-dd fornat
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")

    if start is not None and not is_valid_date(start):
        raise HTTPException(status_code=400, detail="Incorrect 'start' date format must be yyyy-mm-dd.")
    
    if end is not None and not is_valid_date(end):
        raise HTTPException(status_code=400, detail="Incorrect 'end' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()
    ticker_data = await get_hist_price_db(ticker, start, end)

    return ticker_data



async def get_hist_splits(apiKey: str, ticker: str):
    '''
    Returns split data

    :param apiKey: Client api key
    :param ticker: Ticker in str format (ie AAPL)
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    ticker = ticker.upper()
    ticker_data = await get_hist_splits_db(ticker)

    return ticker_data



async def get_hist_divs(apiKey: str, ticker: str):
    '''
    Returns div data

    :param apiKey: Client api key
    :param ticker: Ticker in str format (ie AAPL)
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    ticker = ticker.upper()
    ticker_data = await get_hist_divs_db(ticker)

    return ticker_data



async def get_hist_earnings(apiKey: str, ticker: str):
    '''
    Returns earnings data

    :param apiKey: Client api key
    :param ticker: Ticker in str format (ie AAPL)
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    ticker = ticker.upper()
    ticker_data = await get_hist_earnings_db(ticker)

    return ticker_data