from app.config.db_config import market_db
from fastapi import HTTPException
from datetime import date, datetime
from decimal import Decimal
from app.utils.update_start_date import update_start_date
from app.env import DATA_START_DATE


async def get_tickers_db() -> list:
    '''
    Gets all tickers from db

    :return: tickers list
    '''
    query = 'SELECT ticker FROM stocks ORDER BY ticker;'
    records = await market_db.fetch_all(query)
    tickers = [record['ticker'] for record in records]

    return tickers



async def get_ticker_info_db(ticker: str) -> dict:
    '''
    Gets ticker info from db, excluding img_link, and calculates the most recent date
    the ticker appears in the stock_price table.

    :return: ticker info dict
    '''
    query = '''
    SELECT s.ticker, s.type, s.company_name, s.sector, s.industry, s.exchange, 
           s.region, s.start_date, MAX(sp.date) as end_date
    FROM stocks s
    LEFT JOIN stock_price sp ON s.ticker = sp.ticker
    WHERE s.ticker = :ticker
    GROUP BY s.ticker, s.type, s.company_name, s.sector, s.industry, s.exchange, 
             s.region, s.start_date;
    '''
    record = await market_db.fetch_one(query, values={'ticker': ticker})

    if record:
        data = dict(record)
        update_start_date(data, 'start_date')
        return data
    
    return {}



async def get_hist_price_db(ticker: str, start: str = None, end: str = None) -> dict:
    '''
    Gets historical price info for ticker within range

    :param ticker: Ticker to search for
    :param start: start date to search from
    :param end: end date to search from
    '''
    query = """
    SELECT *
    FROM stock_price sp
    WHERE sp.ticker = :ticker AND sp.date >= :DATA_START_DATE
    AND (
        (CAST(:from_date AS DATE) IS NULL AND CAST(:to_date AS DATE) IS NULL)
        OR
        (sp.date >= CAST(:from_date AS DATE) AND CAST(:to_date AS DATE) IS NULL)
        OR
        (CAST(:from_date AS DATE) IS NULL AND sp.date <= CAST(:to_date AS DATE))
        OR
        (sp.date BETWEEN CAST(:from_date AS DATE) AND CAST(:to_date AS DATE))
    )
    ORDER BY sp.date;
    """
    # Convert string to date object
    if start:
        start_date_obj = datetime.strptime(start, "%Y-%m-%d").date()
    else:
        start_date_obj = None

    if end:
        end_date_obj = datetime.strptime(end, "%Y-%m-%d").date()
    else:
        end_date_obj = None

    records = await market_db.fetch_all(query, values={'ticker': ticker, 'from_date': start_date_obj, 'to_date': end_date_obj, 'DATA_START_DATE': datetime.strptime(DATA_START_DATE, "%Y-%m-%d").date()})
    return [dict(record) for record in records]



async def get_hist_splits_db(ticker: str) -> list:
    '''
    Gets all splits from ticker in db

    :param ticker: string representation of ticker
    :return: splits
    '''
    query = 'SELECT * FROM splits where ticker = :ticker AND date >= :DATA_START_DATE ORDER BY date;'
    records = await market_db.fetch_all(query, values={'ticker': ticker, 'DATA_START_DATE': datetime.strptime(DATA_START_DATE, "%Y-%m-%d").date()})

    return [dict(record) for record in records]


async def get_hist_divs_db(ticker: str) -> list:
    '''
    Gets all divs from ticker in db

    :param ticker: string representation of ticker
    :return: divs
    '''
    query = 'SELECT * FROM dividends where ticker = :ticker AND ex_date >= :DATA_START_DATE ORDER BY ex_date;'
    records = await market_db.fetch_all(query, values={'ticker': ticker, 'DATA_START_DATE': datetime.strptime(DATA_START_DATE, "%Y-%m-%d").date()})

    return [dict(record) for record in records]



async def get_hist_earnings_db(ticker: str) -> list:
    '''
    Gets all earnings from db

    :param ticker: string representation of ticker
    :return: divs
    '''
    query = 'SELECT * FROM earnings where ticker = :ticker AND date >= :DATA_START_DATE ORDER BY date;'
    records = await market_db.fetch_all(query, values={'ticker': ticker, 'DATA_START_DATE': datetime.strptime(DATA_START_DATE, "%Y-%m-%d").date()})

    return [dict(record) for record in records]