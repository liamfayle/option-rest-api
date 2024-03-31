from app.models.options import *
import app.models.stocks as stocks
from app.utils.api_key_check import check_api_key
from app.utils.date_check import is_valid_date
from fastapi import HTTPException
from datetime import datetime



async def get_hist_expiries(apiKey: str, ticker: str, tradeDate: str) -> list:
    '''
    Returns list of avaialble option expiries on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :return: list of expiries
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if tradeDate is not None and not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()
    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()
    ticker_data = await get_hist_expiries_db(ticker, tradeDate)

    return ticker_data



async def get_hist_strikes(apiKey: str, ticker: str, tradeDate: str, expiry: str) -> list:
    '''
    Returns list of avaialble option strikes on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :param expiry: yyyy-mm-dd representaiton of expiry
    :return: list of strikes
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    if expiry is not None and not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'expiry' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()
    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()
    if expiry is not None:
        expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
    ticker_data = await get_hist_strikes_db(ticker, tradeDate, expiry)

    return ticker_data



async def get_hist_price(apiKey: str, ticker: str, tradeDate: str, expiry: str, strike: float, type: str) -> list:
    '''
    Returns list of option prices on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :param expiry: yyyy-mm-dd representaiton of expiry (optional)
    :param strike: float representing option stirke (optional)
    :param type: 'P' or 'C' (optional)
    :return: list of prices
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    if expiry is not None and not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'expiry' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()
    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()
    if expiry is not None:
        expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
    ticker_data = await get_hist_price_db(ticker, tradeDate, expiry, strike, type)

    return ticker_data



async def get_hist_quotes(apiKey: str, ticker: str, tradeDate: str, expiry: str, strike: float, type: str) -> list:
    '''
    Returns list of option quotes on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :param expiry: yyyy-mm-dd representaiton of expiry (optional)
    :param strike: float representing option stirke (optional)
    :param type: 'P' or 'C' (optional)
    :return: list of quotes
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    if expiry is not None and not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'expiry' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()
    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()
    if expiry is not None:
        expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
    ticker_data = await get_hist_quotes_db(ticker, tradeDate, expiry, strike, type)

    return ticker_data




async def get_hist_ivrank(apiKey: str, ticker: str, tradeDate: str, period: int, ivDTE: int) -> list:
    '''
    Returns list of option quotes on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :param period: period for ivr & ivp calcs
    :return: list of ivr
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()

    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()

    ticker_data = await get_hist_ivrank_db(ticker, tradeDate, period, ivDTE)

    return ticker_data



async def get_hist_volcone(apiKey: str, ticker: str, tradeDate: str, period: int, dte: int) -> list:
    '''
    Returns list of option quotes on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :param period: period for ivr & ivp calcs
    :return: list of ivr
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()

    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()

    ticker_data = await get_hist_volcone_db(ticker, tradeDate, period, dte)

    return ticker_data



async def get_hist_earnings(apiKey: str, ticker: str, tradeDate: str) -> list:
    '''
    Returns list of option quotes on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :return: earning data on trade date and before
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()

    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()

    ticker_data = await get_hist_earnings_db(ticker, tradeDate)

    return ticker_data



async def get_hist_ivinfo(apiKey: str, ticker: str, tradeDate: str, expiry: str) -> list:
    '''
    Returns list of option prices on tradeDate

    :param apiKey: Client api key (string format)
    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :param expiry: yyyy-mm-dd representaiton of expiry (optional)
    :return: list of prices
    '''
    api_key_check, auth_level = check_api_key(apiKey)

    if not api_key_check:
        raise HTTPException(status_code=401, detail="Invalid API Key.")
    
    if not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'tradeDate' date format must be yyyy-mm-dd.")
    
    if expiry is not None and not is_valid_date(tradeDate):
        raise HTTPException(status_code=400, detail="Incorrect 'expiry' date format must be yyyy-mm-dd.")
    
    ticker = ticker.upper()
    tradeDate = datetime.strptime(tradeDate, '%Y-%m-%d').date()
    if expiry is not None:
        expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
    ticker_data = await get_hist_ivinfo_db(ticker, tradeDate, expiry)

    return ticker_data