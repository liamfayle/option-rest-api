import numpy as np
from scipy.stats import norm

#https://trading-volatility.com/Trading%20Volatility%20-%20Colin%20Bennett.pdf     PAGE 180 for the below 4 funcs

def forward_vol(sigma1, T1, sigma2, T2):
    '''
    Calculates the foreward volatility between two expirations

    :param sigma1: volatility of nearest option (decimal not %)
    :param T1: Days until exp for nearest option
    :param sigma2: volatility of further option
    :param T2: Days until exp for further option
    :return: forward vol between the two options
    '''
    numerator = ( (sigma2**2) * T2 ) - ( (sigma1**2) * T1 )
    denominator = T2 - T1

    return np.sqrt(numerator / denominator)



def implied_jump_volatility(sigma_diffusive, sigma_exp_after_jump, T):
    '''
    Calculates implied event jump

    :param sigma_diffusive: The diffusive volatility (IV Before jump if there is an expiry before the jump, if not it is sigma12 [ie: the forward vol between to the two exps])
    :param sigma_exp_after_jump: The IV of option most recent after jump
    :param T: the time to expiry (DTE) of expiry after jump (ie dte to sigma_exp_after_jump) option in DAYS
    :return: the implied jump
    '''
    temp = None
    if sigma_diffusive > sigma_exp_after_jump: #THis is bad and should be removed
        temp = sigma_diffusive
        sigma_diffusive = sigma_exp_after_jump
        sigma_exp_after_jump = temp
        print("Triggered bad code in volatility.py")
    return np.sqrt( ( (sigma_exp_after_jump**2) * T ) - ( (sigma_diffusive**2) * (T-1)) )



def implied_ex_earn(total_ivol, implied_jump_vol, T):
    '''
    Calculates volatility with earnings removed

    :param total_ivol: I vol of T'th expiry
    :param implied_jump_vol: the estimated volatility of the jump
    :param T: the time to expiry (DTE) of expiry after jump (ie dte to sigma_exp_after_jump) option in DAYS
    :return: the implied jump
    '''
    return forward_vol(implied_jump_vol, 1, total_ivol, T-1)



def implied_jump_move(implied_jump_vol):
    '''
    Returns absolute percentage move expectred by jump vol

    :param implied_jump_vol: the implied volaility expected by jump
    :return: absolute percentage move
    '''
    return np.sqrt(1/252) * implied_jump_vol * np.sqrt(2 / np.pi)

