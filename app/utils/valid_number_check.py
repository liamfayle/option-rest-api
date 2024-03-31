def is_valid_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
    

def is_valid_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False