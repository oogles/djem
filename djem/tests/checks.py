from django import VERSION


def before_2_1():
    
    return VERSION[0] < 2 or (VERSION[0] == 2 and VERSION[1] == 0)


def after_2_1():
    
    return VERSION[0] > 2 or (VERSION[0] == 2 and VERSION[1] > 0)
