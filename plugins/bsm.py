from scipy.stats import norm
import numpy as np
from py_vollib.black_scholes  import black_scholes as bs
from py_vollib.black_scholes.implied_volatility import implied_volatility as iv
from py_vollib.black_scholes.greeks.analytical import delta 
from py_vollib.black_scholes.greeks.analytical import gamma
from py_vollib.black_scholes.greeks.analytical import rho
from py_vollib.black_scholes.greeks.analytical import theta
from py_vollib.black_scholes.greeks.analytical import vega
import math

# Suppress specific RuntimeWarnings from py_vollib and py_lets_be_rational libraries
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, module='py_vollib.ref_python.black_scholes')
warnings.filterwarnings('ignore', category=RuntimeWarning, module='py_vollib.black_scholes.greeks.analytical')
warnings.filterwarnings('ignore', category=RuntimeWarning, module='py_lets_be_rational.lets_be_rational')




def check_nan(value):
    if value is None or math.isnan(value) or math.isinf(value):
        return None
    return value


'''
    TODO
'''
class BsmOption:
    def __init__(self, isLong, Type, S, K, T, r, sigma=None, value=None, q=0.0):
        '''
        NOTE Only sigma OR value should be passed to the constructor \n

        isLong -> Long / short          [bool]          [False]         Short the option                \n
        Type -> 'P' or 'C'              [Char]          ['P']           Put option                      \n
        S -> Underlying Price           [$]             [100]           100$ Underlying                 \n
        K -> Strike                     [$]             [110]           110$ Strike                     \n
        T -> Time until expiration      [Decimal]       [20]            20 DTE                          \n
        r -> Risk free rate             [Decimal]       [0.01]          1% RFR Continous yield          \n
        sigma -> Volatility             [Decimal]       [0.45]          45% Vol                         \n
        value -> Option Price           [$]             [1.56]          1.56$                           \n
        q -> Dividend Value             [Decimal]       [0.01]          1% Continous Div yield         \n   
        '''
        self.isLong = isLong
        self.Type = Type.lower()
        self.S = S 
        self.K = K
        self.T = T / 365
        self.r = r
        self.q = q
        self.sigma_ = sigma
        self.value = value

        #Get sigma from market price
        if sigma is None:
            try:
                ivol = iv(self.value, self.S, self.K, self.T, self.r, self.Type.lower())
                self.setSigma(ivol)
            except:
                self.setSigma(0.0)

        if value is None:
            self.value = self.price()

        if (type(self.isLong) is not bool or type(self.Type) is not str):
            raise ValueError('Incorrect types for constructor')
        if ( not (self.Type == 'c' or self.Type == 'p')):
            raise ValueError('Must be "P" or "C"')

    

    @property
    def params(self):
        return {'isLong': self.isLong,
                'Type': self.Type,
                'S': self.S,
                'K': self.K,
                'T': self.T,
                'r': self.r,
                'sigma': self.sigma_,
                'value': self.value,
                'q': self.q}


    def delta(self):
        '''
        Return Delta Greek Value \n
        '''
        try:
            return check_nan(delta(self.Type, self.S, self.K, self.T, self.r, self.sigma_))
        except:
            return None
        
    
    def sigma(self):
        try:
            return check_nan(self.sigma_)
        except:
            return None
        

    def gamma(self):
        '''
        Return Gamma Greek Value \n
        '''
        try:
            return check_nan(gamma(self.Type, self.S, self.K, self.T, self.r, self.sigma_))
        except:
            return None

    def vega(self):
        '''
        Return Delta Greek Value \n
        '''
        try:
            return check_nan(vega(self.Type, self.S, self.K, self.T, self.r, self.sigma_))
        except:
            return None


    def theta(self):
        '''
        Return theta Greek Value \n
        '''
        try:
            return check_nan(theta(self.Type, self.S, self.K, self.T, self.r, self.sigma_))
        except:
            return None


    def rho(self):
        '''
        Return rho Greek Value \n
        '''
        try:
            return check_nan(rho(self.Type, self.S, self.K, self.T, self.r, self.sigma_))
        except:
            return None
    

    def price(self):
        '''
        Return price of option \n
        '''
        try:
            return check_nan(bs(self.Type, self.S, self.K, self.T, self.r, self.sigma_))
        except:
            return None


    def setSpot(self, spot):
        '''
        Sets new spot price \n
        '''
        self.S = spot

    def setDTE(self, DTE):
        '''
        Sets new DTE \n
        '''
        self.T = DTE / 365

    def setSigma(self, sigma):
        '''
        Sets new volatility value \n
        '''
        self.sigma_ = sigma



'''
    TODO
        >Add selector for individual option
            *Can then call indivudal update functions that option
'''
class OptionPosition:
    def __init__(self, options=[]):
        '''
        option -> BSM option object LIST \n
        '''
        self.legs = []
        self.shares = 0
        for option in options:
            self.legs.append(option)


    def addLegs(self, options):
        '''
        option -> BSM option object LIST \n
        adds option leg to position \n
        '''
        for option in options:
            self.legs.append(option)

    def addShares(self, shares):
        '''
        shares -> Num shares \n
        adds shares to position \n
        '''
        self.shares += shares

    def removeShares(self, shares):
        '''
        shares -> Num shares \n
        removes shares from position \n
        '''
        self.shares -= shares

    def removeLeg(self, option):
        '''
        option -> BSM option object to be removed \n
        Removes leg from position \n
        '''
        try:
            self.legs.remove(option)
        except Exception as e:
            print(e)

    def getLeg(self, index):
        '''
        Get leg at specified index \n
        '''
        if (index > len(self.legs)):
            raise Exception("Cannot get index greater than size")

        return self.legs[index]

    def price(self):
        '''
        Returns current theoretical price of position \n
        '''
        value = 0
        for leg in self.legs:
            value += leg.price()
        return value

    def delta(self):
        '''
        Returns current delta of position \n
        '''
        value = 0
        for leg in self.legs:
            value += leg.delta()
        value += (self.shares/100)
        return value

    def gamma(self):
        '''
        Returns current gamma of position \n
        '''
        value = 0
        for leg in self.legs:
            value += leg.gamma()
        return value

    def vega(self):
        '''
        Returns current vega of position \n
        '''
        value = 0
        for leg in self.legs:
            value += leg.vega()
        return value

    def theta(self):
        '''
        Returns current theta of position \n
        '''
        value = 0
        for leg in self.legs:
            value += leg.theta()
        return value

    def rho(self):
        '''
        Returns current rho of position \n
        '''
        value = 0
        for leg in self.legs:
            value += leg.rho()
        return value

    def sigma(self):
        '''
        Returns average sigma of position \n
        '''
        value = 0
        for leg in self.legs:
            value += leg.sigma
        return value / len(self.legs)


    def updateDTE(self, DTE):
        '''
        Updates DTE of !ALL! options in position \n
        '''
        for leg in self.legs:
            leg.setDTE(DTE)

    def updateSigma(self, DTE):
        '''
        Updates DTE of !ALL! options in position \n
        '''
        for leg in self.legs:
            leg.setSigma(DTE)

    def updateSpot(self, spot):
        '''
        Updates Spot price of !ALL! options in position \n
        '''
        for leg in self.legs:
            leg.setSpot(spot)

    def updateSpotReturnPrice(self, spot):
        '''
        Updates Spot price of !ALL! options in position and returns new price \n
        '''
        for leg in self.legs:
            leg.setSpot(spot)
        return self.price()

    def getSpot(self):
        '''
        Return spot price of first leg.
        '''
        return self.legs[0].S
    
    def getR(self):
        '''
        Return RFR of first leg.
        '''
        return self.legs[0].r

    def getDTE(self):
        '''
        Return DTE of first leg
        '''
        return self.legs[0].T * 365

    


    




 