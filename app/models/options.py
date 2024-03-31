from time import time
from tokenize import group
from xmlrpc.client import Boolean
from app.config.db_config import market_db
from datetime import datetime, timedelta
from plugins.bsm import BsmOption, OptionPosition
from app.env import DATA_START_DATE
from collections import defaultdict
import numpy as np
import io
from contextlib import redirect_stdout
from scipy.interpolate import UnivariateSpline
from decimal import Decimal
from app.utils.volatility import forward_vol, implied_jump_volatility, implied_ex_earn, implied_jump_move


class TextTrap(io.StringIO):
    def write(self, s):
        # Override write method to do nothing
        pass


async def get_hist_expiries_db(ticker: str, tradeDate: str) -> list:
    '''
    Gets historical expiries on date

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :return: list of expiries
    '''
    query = '''
    SELECT options.expiry_date
    FROM options
    JOIN option_price ON options.option_id = option_price.option_id
    WHERE options.ticker = :ticker AND option_price.date = :tradeDate;
    '''
    records = await market_db.fetch_all(query, values={'ticker': ticker, 'tradeDate': tradeDate})
    return list(set([record['expiry_date'] for record in records]))



async def get_hist_strikes_db(ticker: str, tradeDate: str, expiry: str = None) -> dict:
    '''
    Gets historical strikes on date.

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representation of tradeDate
    :param expiry: yyyy-mm-dd representation of expiry (optional)
    :return: dict with trade dates as keys and list of strikes as values
    '''
    if expiry:
        query = '''
        SELECT 
            options.expiry_date, 
            options.strike,
            COALESCE(EXP(SUM(LN(option_splits.adjustment_factor))), 1) AS total_adjustment_factor
        FROM options
        JOIN option_price ON options.option_id = option_price.option_id
        LEFT JOIN option_splits ON options.option_id = option_splits.option_id AND :tradeDate >= option_splits.split_date
        WHERE options.ticker = :ticker AND option_price.date = :tradeDate AND options.expiry_date = :expiry AND options.type = 'C'
        GROUP BY options.expiry_date, options.strike
        ORDER BY options.expiry_date;
        '''
        records = await market_db.fetch_all(query, values={'ticker': ticker, 'tradeDate': tradeDate, 'expiry': expiry})
    else:
        query = '''
        SELECT 
            options.expiry_date, 
            options.strike,
            options.adj_strike
            COALESCE(EXP(SUM(LN(option_splits.adjustment_factor))), 1) AS total_adjustment_factor
        FROM options
        JOIN option_price ON options.option_id = option_price.option_id
        LEFT JOIN option_splits ON options.option_id = option_splits.option_id AND :tradeDate >= option_splits.split_date
        WHERE options.ticker = :ticker AND option_price.date = :tradeDate AND options.type = 'C'
        GROUP BY options.expiry_date, options.strike, options.adj_strike
        ORDER BY options.expiry_date, options.adj_strike;
        '''
        records = await market_db.fetch_all(query, values={'ticker': ticker, 'tradeDate': tradeDate})

    # Aggregate strikes by expiry date
    strikes_by_date = {}
    for record in records:
        date = record['expiry_date']
        strike = round(float(record['strike'] / record['total_adjustment_factor']), 2)
        if date in strikes_by_date:
            strikes_by_date[date].append(strike)
        else:
            strikes_by_date[date] = [strike]

    # Ensure the strikes are unique and sorted for each date
    for date in strikes_by_date:
        strikes_by_date[date] = sorted(set(strikes_by_date[date]))

    return strikes_by_date




async def get_hist_price_db(ticker: str, tradeDate: str, expiry: str = None, strike: float = None, type: str = None, trim: Boolean = True) -> dict:
    '''
    Gets historical prices on date.

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representation of tradeDate
    :param expiry: yyyy-mm-dd representation of expiry (optional)
    :param strike: strike price (optional)
    :param type: 'P' or 'C' (optional)
    :return: dict with expiry dates as keys and list of bid-ask price pairs as values
    '''
    query = '''
    SELECT 
        options.expiry_date, 
        options.strike, 
        options.adj_strike,
        options.type, 
        option_price.spot_price,
        option_price.interpolated_value,
        option_price.irate, 
        COALESCE(EXP(SUM(LN(option_splits.adjustment_factor))), 1) AS total_adjustment_factor
    FROM options
    JOIN option_price ON options.option_id = option_price.option_id
    LEFT JOIN option_splits ON options.option_id = option_splits.option_id AND :tradeDate >= option_splits.split_date
    WHERE options.ticker = :ticker AND option_price.date = :tradeDate
    '''

    values = {'ticker': ticker, 'tradeDate': tradeDate}

    if expiry:
        query += ' AND options.expiry_date = :expiry'
        values['expiry'] = expiry

    if type is not None:
        query += ' AND options.type = :type'
        values['type'] = type

    query += ' GROUP BY options.expiry_date, options.strike, options.adj_strike, options.type, option_price.spot_price, option_price.irate, option_price.interpolated_value'
    query += ' ORDER BY options.expiry_date ASC, options.adj_strike ASC;'
    records = await market_db.fetch_all(query, values=values)

    prices_by_date = defaultdict(lambda: {'C': [], 'P': []})

    for record in records:
        record = dict(record)
        date = record.get('expiry_date')

        if strike is not None and abs(float(record['strike'] / record['total_adjustment_factor']) - float(strike)) > 0.015:
            continue

        if date:
            dte = abs((tradeDate - date).days)
            date = str(date)

            with redirect_stdout(TextTrap()):
                option = BsmOption(True, record['type'], float(record['spot_price']), round(float(record['strike'] / record['total_adjustment_factor']), 2), dte, float(record['irate']) if record['irate'] else 0, value=round(float(record['interpolated_value']), 2))
                
                if option.sigma() == 0:
                    continue

                option_data = {
                    'strike': round(float(record['strike'] / record['total_adjustment_factor']), 2), 
                    'type': record['type'], 
                    'num_shares': int(round(100 * float(record['total_adjustment_factor']), 0)),
                    'spot_price': float(record['spot_price']),
                    'contract_price': round(float(record['interpolated_value']), 2),
                    'ivol': option.sigma(),
                    'delta': option.delta(),
                    'gamma': option.gamma(),
                    'vega': option.vega(),
                    'theta': option.theta(),
                    'rho': option.rho()
                }

                if record['type'] == 'C':
                    prices_by_date[date]['C'].append(option_data)
                elif record['type'] == 'P':
                    prices_by_date[date]['P'].append(option_data)

    return dict(prices_by_date)




async def get_hist_quotes_db(ticker: str, tradeDate: str, expiry: str = None, strike: float = None, type: str = None, trim: str = False) -> dict:
    '''
    Gets historical quotes on date.

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representation of tradeDate
    :param expiry: yyyy-mm-dd representation of expiry (optional)
    :param strike: strike price (optional)
    :param type: 'P' or 'C' (optional)
    :return: dict with expiry dates as keys and list of bid-ask price pairs as values
    '''
    query = '''
    SELECT 
        options.expiry_date, 
        options.strike, 
        options.adj_strike,
        options.type, 
        option_price.spot_price,
        option_price.bid_price, 
        option_price.ask_price, 
        option_price.interpolated_value, 
        option_price.volume, 
        option_price.open_interest, 
        option_price.irate, 
        option_price.ask_iv, 
        COALESCE(EXP(SUM(LN(option_splits.adjustment_factor))), 1) AS total_adjustment_factor
    FROM options
    JOIN option_price ON options.option_id = option_price.option_id
    LEFT JOIN option_splits ON options.option_id = option_splits.option_id AND :tradeDate >= option_splits.split_date
    WHERE options.ticker = :ticker AND option_price.date = :tradeDate
    '''

    values = {'ticker': ticker, 'tradeDate': tradeDate}

    if expiry:
        query += ' AND options.expiry_date = :expiry'
        values['expiry'] = expiry

    if type is not None:
        query += ' AND options.type = :type'
        values['type'] = type

    if trim:
        query += ' AND options.bid_price != 0'

    query += ' GROUP BY options.expiry_date, options.strike, options.adj_strike, option_price.spot_price, option_price.interpolated_value, option_price.volume, option_price.open_interest, options.type, option_price.bid_price, option_price.ask_price, option_price.irate, option_price.ask_iv'
    query += ' ORDER BY options.expiry_date ASC, options.adj_strike ASC;'
    records = await market_db.fetch_all(query, values=values)

    prices_by_date = defaultdict(lambda: {'C': [], 'P': []})

    for record in records:
        record = dict(record)
        date = record.get('expiry_date')

        if strike is not None and abs(float(record['strike'] / record['total_adjustment_factor']) - float(strike)) > 0.015:
            continue

        if date:
            mid_price = (record['bid_price'] + record['ask_price']) / 2
            if record['bid_price'] == 0:
                mid_price = record['ask_price']
            elif record['ask_price'] == 0:
                mid_price = record['bid_price']

            dte = abs((tradeDate - date).days)
            date = str(date)

            with redirect_stdout(TextTrap()):
                bid_option = BsmOption(True, record['type'], float(record['spot_price']), round(float(record['strike'] / record['total_adjustment_factor']), 2), dte, float(record['irate']) if record['irate'] else 0, value=round(float(record['bid_price']), 2))
                mid_option = BsmOption(True, record['type'], float(record['spot_price']), round(float(record['strike'] / record['total_adjustment_factor']), 2), dte, float(record['irate']) if record['irate'] else 0, value=round(float(mid_price), 2))
                interpolated_option = BsmOption(True, record['type'], float(record['spot_price']), round(float(record['strike'] / record['total_adjustment_factor']), 2), dte, float(record['irate']) if record['irate'] else 0, value=round(float(record['interpolated_value']), 2))
                ask_option = BsmOption(True, record['type'], float(record['spot_price']), round(float(record['strike'] / record['total_adjustment_factor']), 2), dte, float(record['irate']) if record['irate'] else 0, value=round(float(record['ask_price']), 2))

                option_data = {
                    'strike': round(float(record['strike'] / record['total_adjustment_factor']), 2), 
                    'type': record['type'], 
                    'num_shares': int(round(100 * float(record['total_adjustment_factor']), 0)),
                    'bid_price': round(float(record['bid_price']), 2),
                    'bid_ivol': bid_option.sigma(),
                    'bid_delta': bid_option.delta(),
                    'bid_gamma': bid_option.gamma(),
                    'bid_vega': bid_option.vega(),
                    'bid_theta': bid_option.theta(),
                    'bid_rho': bid_option.rho(),
                    'mid_price': round(float(mid_price), 2),
                    'mid_ivol': mid_option.sigma(),
                    'mid_delta': mid_option.delta(),
                    'mid_gamma': mid_option.gamma(),
                    'mid_vega': mid_option.vega(),
                    'mid_theta': mid_option.theta(),
                    'mid_rho': mid_option.rho(),
                    'interpolated_price': round(float(record['interpolated_value']), 2),
                    'interpolated_ivol': interpolated_option.sigma(),
                    'interpolated_delta': interpolated_option.delta(),
                    'interpolated_gamma': interpolated_option.gamma(),
                    'interpolated_vega': interpolated_option.vega(),
                    'interpolated_theta': interpolated_option.theta(),
                    'interpolated_rho': interpolated_option.rho(),
                    'ask_price': round(float(record['ask_price']), 2),
                    'ask_ivol': ask_option.sigma(),
                    'ask_delta': ask_option.delta(),
                    'ask_gamma': ask_option.gamma(),
                    'ask_vega': ask_option.vega(),
                    'ask_theta': ask_option.theta(),
                    'ask_rho': ask_option.rho()
                }

                if record['type'] == 'C':
                    prices_by_date[date]['C'].append(option_data)
                elif record['type'] == 'P':
                    prices_by_date[date]['P'].append(option_data)

    return dict(prices_by_date)




async def is_date_valid(date: str):
    '''
    Checks if date is valid
    '''
    if str(date) < DATA_START_DATE:
        return False

    q = f"""
        SELECT *
        FROM dates_processed
        WHERE dates_processed.date = :date;
    """

    date = datetime.strptime(date, '%Y-%m-%d').date()
    days = await market_db.fetch_all(q, values={'date': date})

    return len(days) > 0


async def get_hist_ivrank_db(ticker: str, tradeDate: str, lookback_period: int, ivDTE: int) -> list:
    '''
    Gets historical IV rank & IV percentile on date.

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representation of tradeDate
    :param lookback_period: number of days to look back
    :param ivDTE: the IV to use. i.e., if 30, it should use the 30 DTE option expiry
    :return: list of IVR and IVP
    '''
    days_q = f"""
        SELECT *
        FROM dates_processed
        WHERE dates_processed.date <= :tradeDate
        ORDER BY dates_processed.date DESC
        LIMIT :n;
    """

    days = await market_db.fetch_all(days_q, values={'tradeDate': tradeDate, 'n': lookback_period + 1})
    days = [d.date for d in days]

    end_date = days[-1]

    if str(end_date) < DATA_START_DATE:
        end_date = datetime.strptime(DATA_START_DATE, '%Y-%m-%d')

    # SQL query to fetch options data
    query = f"""
        SELECT *
        FROM stock_iv
        WHERE ticker = :ticker 
            AND trade_date >= :end_date
            AND trade_date <= :tradeDate
            AND dte > 0
        ORDER BY trade_date
    """
    
    data = await market_db.fetch_all(query, values={'tradeDate': tradeDate, 'ticker': ticker, 'end_date': end_date})
    data = [convert_decimal_to_float(dict(x)) for x in data]

    splines = fit_spline_skew(data)
    term_structure = fit_spline_term_structure(splines)

    ivs = np.array([float(spline(ivDTE)) for date, spline in term_structure.items()])
    
    if len(ivs) == 0:
        return []

    current_iv = ivs[-1]
    max_iv = np.max(ivs)
    min_iv = np.min(ivs)

    iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100 if max_iv != min_iv else 0

    num_days_with_lower_iv = np.sum(iv < current_iv for iv in ivs)
    iv_percentile = ((num_days_with_lower_iv+1) / len(ivs)) * 100
    

    return {
        'iv_rank': round(iv_rank, 4),
        'iv_percentile': round(iv_percentile, 4)
    }



async def get_hist_volcone_db(ticker: str, tradeDate: str, lookback_period: int, dte: int) -> list:
    '''
    Gets historical vol cone on date

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representation of tradeDate
    :param lookback_period: number of days to look back
    :param dte: the IV to use. i.e., if 30, it should use the 30 DTE option expiry
    :return: vol cone data
    '''
    days_q = f"""
        SELECT *
        FROM dates_processed
        WHERE dates_processed.date <= :tradeDate
        ORDER BY dates_processed.date DESC
        LIMIT :n;
    """

    days = await market_db.fetch_all(days_q, values={'tradeDate': tradeDate, 'n': lookback_period + 1})
    days = [d.date for d in days]

    end_date = days[-1]

    if str(end_date) < DATA_START_DATE:
        end_date = datetime.strptime(DATA_START_DATE, '%Y-%m-%d')

    # SQL query to fetch options data
    query = f"""
        SELECT *
        FROM stock_iv
        WHERE ticker = :ticker 
            AND trade_date >= :end_date
            AND trade_date <= :tradeDate
            AND dte > 0
        ORDER BY trade_date
    """
    
    data = await market_db.fetch_all(query, values={'tradeDate': tradeDate, 'ticker': ticker, 'end_date': end_date})
    data = [convert_decimal_to_float(dict(x)) for x in data]

    splines = fit_spline_skew(data)
    term_structure = fit_spline_term_structure(splines)

    ivs = np.array([float(spline(dte)) for date, spline in term_structure.items()])

    if len(ivs) == 0:
        return []
    
    current_iv = ivs[-1]

    max_iv = np.max(ivs)
    min_iv = np.min(ivs)

    median_iv = np.median(ivs)
    mean_iv = np.mean(ivs)
    std_iv = np.std(ivs)

    quants_iv = np.quantile(ivs, [.10, .20, .30, .40, .60, .70, .80, .90])
    
    returnable = {
        'current_iv': current_iv,
        'stdev': std_iv,
        'mean': mean_iv,
        '0%': min_iv,
        '10%': quants_iv[0],
        '20%': quants_iv[1],
        '30%': quants_iv[2],
        '40%': quants_iv[3],
        '50%': median_iv,
        '60%': quants_iv[4],
        '70%': quants_iv[5],
        '80%': quants_iv[6],
        '90%': quants_iv[7],
        '100%': max_iv,
    }

    for key, value in returnable.items():
        returnable[key] = round(value, 4)

    return returnable



async def get_hist_earnings_db(ticker: str, tradeDate: str) -> list:
    '''
    Gets historical earnings data on and before date

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representaiton of tradeDate
    :return: earnings data
    '''

    realized_q = """
        WITH earnings_data AS (
        SELECT earnings.date, earnings.time
        FROM earnings
        WHERE earnings.ticker = :ticker AND earnings.date <= :tradeDate
        AND (earnings.time = 'bmo' OR earnings.time = 'amc')
        ORDER BY earnings.date ASC
    )
    SELECT
        e.date AS earnings_date,
        e.time AS earnings_time,
        CASE 
            WHEN e.time = 'bmo' THEN
                (
                    SELECT p.close
                    FROM stock_price p
                    WHERE p.ticker = :ticker AND p.date < e.date
                    ORDER BY p.date DESC
                    LIMIT 1
                )
            ELSE NULL
        END AS prev_close,
        (
            SELECT p.open
            FROM stock_price p
            WHERE p.ticker = :ticker AND p.date = e.date
        ) AS earnings_open,
        (
            SELECT p.close
            FROM stock_price p
            WHERE p.ticker = :ticker AND p.date = e.date
        ) AS earnings_close,
        CASE 
            WHEN e.time = 'amc' THEN
                (
                    SELECT p.open
                    FROM stock_price p
                    WHERE p.ticker = :ticker AND p.date > e.date
                    ORDER BY p.date ASC
                    LIMIT 1
                )
            ELSE NULL
        END AS next_open,
        CASE 
            WHEN e.time = 'amc' THEN
                (
                    SELECT p.close
                    FROM stock_price p
                    WHERE p.ticker = :ticker AND p.date > e.date
                    ORDER BY p.date ASC
                    LIMIT 1
                )
            ELSE NULL
        END AS next_close
    FROM earnings_data e
    """
    moves = await market_db.fetch_all(realized_q, values={'ticker': ticker, 'tradeDate': tradeDate})

    price_data = []
    earnings_data = {'earnings': []}
    for record in moves:
        price_data.append({
            'spot_before': record['prev_close'] if record['earnings_time'] == "bmo" else record['earnings_close'],
            'spot_after': record['earnings_close'] if record['earnings_time'] == "bmo" else record['next_close']
        })

        earnings_data['earnings'].append({
            'earnings_date': record['earnings_date'],
            'earnings_time': record['earnings_time'],
            'realized_jump': 
                (record['earnings_open'] - record['prev_close']) / record['prev_close'] if record['earnings_time'] == "bmo" else
                (record['next_open'] - record['earnings_close']) / record['earnings_close'],
            'realized_move': 
                (record['earnings_close'] - record['prev_close']) / record['prev_close'] if record['earnings_time'] == "bmo" else
                (record['next_close'] - record['earnings_close']) / record['earnings_close'],
        })

    iv_q = """
    WITH earnings_data AS (
        SELECT earnings.date, earnings.time
        FROM earnings
        WHERE earnings.ticker = :ticker AND earnings.date <= :tradeDate
        AND (earnings.time = 'bmo' OR earnings.time = 'amc')
        ORDER BY earnings.date ASC
        )
    SELECT *
        FROM earnings_data e
        JOIN stock_iv iv ON iv.ticker = :ticker AND (
            (e.time = 'bmo' AND iv.trade_date = (
                SELECT MAX(trade_date)
                FROM stock_iv
                WHERE ticker = :ticker AND trade_date < e.date
            )) OR 
            (e.time = 'amc' AND iv.trade_date = e.date)
        )
        ORDER BY iv.trade_date, iv.dte, iv.moneyness
    """
    data = await market_db.fetch_all(iv_q, values={'ticker': ticker, 'tradeDate': tradeDate})
    data = [convert_decimal_to_float(dict(x)) for x in data]
    splines = fit_spline_skew(data)

    for i, date in enumerate(splines):
        dtes = list(splines[date].keys())
        ivs = list(splines[date].values())

        if len(dtes) < 3 or len(ivs) < 3:
            earnings_data[i]['abs_implied_move'] = None

        c = 0
        if dtes[0] == 1:
            c = 1

        near_dte = dtes[0+c]
        far_dte = dtes[1+c]
        near_spline = ivs[0+c]
        far_spline = ivs[1+c]

        sigma12 = forward_vol(near_spline(0.5), near_dte, far_spline(0.5), far_dte)
        sigma_jump = implied_jump_volatility(sigma12, far_spline(0.5), far_dte)
        ex_earn_vol = implied_ex_earn(near_spline(0.5), sigma_jump, near_dte) if near_dte > 2 else sigma12 #Due to how ex earn is calculated it must be 3 dte atleast
        earnings_data['earnings'][i]['abs_implied_move'] = implied_jump_move(sigma_jump)

        before_straddle = OptionPosition()
        call = BsmOption(True, 'C', float(price_data[i]['spot_before']), float(price_data[i]['spot_before']), near_dte, 0.0, sigma=near_spline(0.5))
        put = BsmOption(True, 'P', float(price_data[i]['spot_before']), float(price_data[i]['spot_before']), near_dte, 0.0, sigma=near_spline(0.5))
        before_straddle.addLegs([call, put])

        after_straddle = OptionPosition()
        call = BsmOption(True, 'C', float(price_data[i]['spot_after']), float(price_data[i]['spot_before']), near_dte-1, 0.0, sigma=ex_earn_vol)
        put = BsmOption(True, 'P', float(price_data[i]['spot_after']), float(price_data[i]['spot_before']), near_dte-1, 0.0, sigma=ex_earn_vol)
        after_straddle.addLegs([call, put])

        earnings_data['earnings'][i]['straddle_return'] =  (after_straddle.price() - before_straddle.price()) / before_straddle.price() #Calculate % change in price


    if len(earnings_data['earnings']) > 0:
        avg_realized_move = np.mean([abs(x['realized_move']) for x in earnings_data['earnings']])
        avg_realized_jump = np.mean([abs(x['realized_jump']) for x in earnings_data['earnings']])
        avg_implied_move = np.mean([abs(x['abs_implied_move']) for x in earnings_data['earnings']])
        avg_straddle_return = np.mean([x['straddle_return'] for x in earnings_data['earnings']])
        cumulative_straddle_return = np.cumsum([x['straddle_return'] for x in earnings_data['earnings']])[-1]

        earnings_data['avg_abs_realized_move'] = avg_realized_move
        earnings_data['avg_abs_realized_jump'] = avg_realized_jump
        earnings_data['avg_abs_implied_move'] = avg_implied_move
        earnings_data['avg_straddle_return'] = avg_straddle_return
        earnings_data['cumulative_straddle_return'] = cumulative_straddle_return      

    return earnings_data




async def get_hist_ivinfo_db(ticker: str, tradeDate: str, expiry: str) -> list:
    '''
    Gets various iv metrics

    :param ticker: ticker to get option data for
    :param tradeDate: yyyy-mm-dd representation of tradeDate
    :param expiry: yyy-mm-dd date
    :return: iv metrics
    '''
    selected_dte = None
    if expiry is not None:
        selected_dte = int((expiry - tradeDate) / timedelta(days=1))

    values = {'ticker': ticker, 'tradeDate': tradeDate}

    query = """
        SELECT *
        FROM earnings
        WHERE ticker = :ticker and date > :tradeDate
        ORDER BY date ASC
        LIMIT 1;
    """
    earnings_date = await market_db.fetch_one(query, values=values)
    earnings_date = earnings_date['date']
    earnings_dte = int( (earnings_date - tradeDate) / timedelta(days=1) )

    query = """
        SELECT * 
        FROM stock_iv
        WHERE ticker = :ticker AND trade_date = :tradeDate
        ORDER BY dte, moneyness;
    """

    data = await market_db.fetch_all(query, values=values)
    data = [convert_decimal_to_float(dict(x)) for x in data]
    splines = fit_spline_skew(data)

    if not splines:
        return {}

    _, first_splines = next(iter(splines.items()))

    iv_info = {'expiries': {}}
    check = 0
    near_dte = far_dte = near_spline = far_spline = None
    for dte in first_splines:
        spline = first_splines[dte]
        expiry = str(tradeDate + timedelta(days=dte))

        if check == 1 and dte > earnings_dte:
            check += 1
            far_dte = dte
            far_spline = spline
        if check == 0 and dte > earnings_dte:
            check += 1
            near_dte = dte
            near_spline = spline
            

        _0_100_skew = spline(0) / spline(1) #put / call
        _25_75_skew = spline(.25) / spline(.75) #put / call
        _25_50_skew = spline(.25) / spline(.5) #put / atm
        _0_50_skew = spline(0) / spline(.5) #put / atm
        _50_75_skew = spline(.5) / spline(.75) #atm / call
        _50_100_skew = spline(.5) / spline(1) #atm / call

        implied_daily_move = spline(0.5) / np.sqrt(252)

        iv_info['expiries'][expiry] = {
            'dte': dte,
            'iv0': float(spline(0)),
            'iv10': float(spline(.10)),
            'iv20': float(spline(.20)),
            'iv30': float(spline(.30)),
            'iv40': float(spline(.40)),
            'iv50': float(spline(.50)),
            'iv60': float(spline(.60)),
            'iv70': float(spline(.70)),
            'iv80': float(spline(.80)),
            'iv90': float(spline(.90)),
            'iv100': float(spline(1)),
            '0_100_skew': _0_100_skew,
            '25_75_skew': _25_75_skew,
            '25_50_skew': _25_50_skew,
            '0_50_skew': _0_50_skew,
            '50_75_skew': _50_75_skew,
            '50_100_skew': _50_100_skew,
            'implied_daily_move': implied_daily_move
        }
        
    sigma12 = forward_vol(near_spline(0.5), near_dte, far_spline(0.5), far_dte)
    sigma_jump = implied_jump_volatility(sigma12, far_spline(0.5), far_dte)
    implied_earning_move = implied_jump_move(sigma_jump)

    iv_info['next_earnings_date'] = earnings_date
    iv_info['next_earnings_dte'] = earnings_dte
    iv_info['next_earnings_implied_move'] = implied_earning_move

    dtes = list(first_splines.keys())
    iv_info['term_structure_slope'] = first_splines[dtes[0]](0.5) / first_splines[dtes[-1]](0.5) if len(dtes) > 1 else None


    for dte in first_splines:
        spline = first_splines[dte]
        expiry = str(tradeDate + timedelta(days=dte))

        if dte > earnings_dte:
            iv_info['expiries'][expiry]['iv_earnings_removed'] = implied_ex_earn(spline(0.5), sigma_jump, dte) if dte > 2 else sigma12
        else:
            iv_info['expiries'][expiry]['iv_earnings_removed'] = float(spline(0.5))

    return iv_info




###HELPERS
def convert_decimal_to_float(item):
    """
    Recursively converts all decimal.Decimal types to float in a dictionary.

    :param item: The dictionary or value to convert.
    :return: The item with all decimal.Decimal types converted to float.
    """
    if isinstance(item, dict):
        return {k: convert_decimal_to_float(v) for k, v in item.items()}
    if isinstance(item, list):
        return [convert_decimal_to_float(v) for v in item]
    if isinstance(item, Decimal):
        return float(item)
    return item


def fit_spline_skew(data):
    """
    Fits a spline for each unique 'dte' value in the data, 
    keeping only unique actual_moneyness values and ignoring nulls.

    :param data: List of dictionaries with keys 'dte', 'actual_moneyness', and 'iv'.
    :return: Dictionary of splines for each unique 'dte'.
    """
    # Group data by 'dte', keeping only unique actual_moneyness values and ignoring nulls
    grouped_data = {}
    for item in data:
        # Ignore if actual_moneyness or iv is null
        if item['actual_moneyness'] is None or item['iv'] is None:
            continue

        date = str(item['trade_date'])
        dte = item['dte']
        actual_moneyness = item['actual_moneyness']
        iv = item['iv']

        if date not in grouped_data:
            grouped_data[date] = {}

        if dte not in grouped_data[date]:
            grouped_data[date][dte] = {'x': [], 'y': [], 'w': []}
        
        # Keep only one data point if actual_moneyness is equal
        if actual_moneyness not in grouped_data[date][dte]['x']:
            grouped_data[date][dte]['x'].append(actual_moneyness)
            grouped_data[date][dte]['y'].append(iv)
            # Assign a default weight (e.g., 1)
            grouped_data[date][dte]['w'].append(1) 

    # Fit spline for each group
    splines = {}
    for date in grouped_data.keys():
        for dte, values in grouped_data[date].items():
            x = np.array(values['x'])
            y = np.array(values['y'])
            w = np.array(values['w'])

            # Find index of the point closest to x = 0.5
            closest_index = np.argmin(np.abs(x - 0.5))
            # Increase the weight for this point
            w[closest_index] *= 10  # You can adjust this factor

            # Ensure data is sorted by x (actual_moneyness)
            sorted_indices = np.argsort(x)
            x_sorted = x[sorted_indices]
            y_sorted = y[sorted_indices]
            w_sorted = w[sorted_indices]

            # Fit spline if there are enough data points
            if len(x_sorted) > 1:  # for linear spline (k=1)
                spline = UnivariateSpline(x_sorted, y_sorted, w=w_sorted, s=0, k=1, ext=3)
                if date not in splines:
                    splines[date] = {}
                splines[date][dte] = spline

    return splines


def fit_spline_term_structure(splines, moneyness=0.5):
    """
    Fits a new spline to create a term structure curve using DTE as x values and the IV at actual_moneyness 0.5 as y values.
    
    :param splines: Dictionary of splines for each unique 'dte' organized by 'trade_date'.
    :return: Dictionary with a term structure spline for each trade date.
    """
    term_structure_splines = {}
    for date, splines_by_dte in splines.items():
        dte_values = []
        iv_values = []
        for dte, spline in splines_by_dte.items():
            # Evaluate the spline at actual_moneyness of 0.5 and collect IVs
            iv_at_0_5 = spline(moneyness)
            dte_values.append(dte)
            iv_values.append(iv_at_0_5)
        
        # Convert DTE and IV lists to numpy arrays
        dte_values = np.array(dte_values)
        iv_values = np.array(iv_values)
        
        # Sort the arrays based on DTE
        sorted_indices = np.argsort(dte_values)
        dte_values_sorted = dte_values[sorted_indices]
        iv_values_sorted = iv_values[sorted_indices]
        
        # Fit a new spline to the term structure data
        if len(dte_values_sorted) > 1:
            term_structure_spline = UnivariateSpline(dte_values_sorted, iv_values_sorted, k=1, s=0, ext=3)
            term_structure_splines[date] = term_structure_spline
    
    return term_structure_splines



import matplotlib.pyplot as plt
def plot_spline_and_data(data):
    """
    Plot a spline and its underlying fitted data points for one 'dte' value from the data.
    This version converts Decimal types to float.

    :param data: List of dictionaries with keys 'dte', 'actual_moneyness', and 'iv'.
    """

    # Use the modified function to fit spline
    splines = fit_spline_skew(data)

    # Choose one spline to plot (if available)
    for date in splines.keys():
        for dte, spline in splines[date].items():

            # Extract original data points for the chosen dte
            x_points = [item['actual_moneyness'] for item in data if item['dte'] == dte and str(item['trade_date']) == date]
            y_points = [item['iv'] for item in data if item['dte'] == dte and str(item['trade_date']) == date]

            # Generate a range of x values for plotting the spline
            x_range = np.linspace(0, 1, 100)


            # Plot the spline and the original data points
            plt.figure(figsize=(10, 6))
            plt.plot(x_range, spline(x_range), label=f"Spline for DTE {dte}")
            plt.scatter(x_points, y_points, color='red', label="Original Data Points")
            plt.xlabel("Actual Moneyness")
            plt.ylabel("IV")
            plt.title(f"DTE {dte} -- TradeDate {date}")
            plt.legend()
            plt.show()


def plot_term_structure(term_structure_splines):
    """
    Plot the term structure of IV for a given trade date.

    :param term_structure_splines: Dictionary with a term structure spline for each trade date.
    :param trade_date: The trade date to plot the term structure for.
    :param dte_range: Optional range of DTE values for plotting. If None, it will be calculated from the data.
    """
    for trade_date in term_structure_splines:
        term_structure_spline = term_structure_splines[trade_date]

        # Generate a range of x values for plotting the spline
        x_range = np.linspace(0, 700, 100)

        # Plot the term structure
        plt.figure(figsize=(10, 6))
        plt.plot(x_range, term_structure_spline(x_range), label=f"Term Structure for TradeDate {trade_date}")
        plt.xlabel("Days to Expiration (DTE)")
        plt.ylabel("Implied Volatility (IV)")
        plt.title(f"Term Structure of IV - TradeDate {trade_date}")
        plt.legend()
        plt.grid(True)
        plt.show()



#TODO Fundamental data
#TODO Live data