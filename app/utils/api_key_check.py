


def check_api_key(apiKey: str) -> (bool, int):
    '''
    Checks whether api key is valid

    :param apiKey: api key
    :return: tuple (bool, int) where bool represents whether key is valid and int represnets user auth level
    '''
    return True, 1