from app.env import DATA_START_DATE


def update_start_date(dict: dict, key: str) -> None:
    '''
    Changes the date to start date if smaller than environment var
    '''
    if str(dict[key]) < DATA_START_DATE:
        dict[key] = DATA_START_DATE
        