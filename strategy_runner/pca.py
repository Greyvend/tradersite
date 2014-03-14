__author__ = 'mosin'
import numpy as np
import numpy.matlib as ml
from numpy.linalg import eig

#Parameters
k = 5  # amount of eigenvectors to consider. Defines the risk factors that we
       # take into account
H = 10  # amount of time periods to analyze
time_shift = 0  # time shift from the last moment. The more t, the older PCAs
                # are analyzed (0 for current time)
epsilon = 0  # Treshold parameter
regime_switcher = True  # Boolean parameter, enables regime switcher


def signal(prices, index):
    """
    Signals to buy/sell stocks.

    Returns tuple (X1, X2, ..., Xn), where n is amount of stocks,
    Xi is one of the ('sell', 'buy', None).
    :param prices: list of price lists of stocks, in time ascending order
    :param index: list of k(!) price lists of benchmark values for k last
    periods, in time ascending order, with same time frame as stocks.
    """
    def betas(prices_m):
        """
        Count beta parameters for all stocks, described in 'prices_m' matrix,
        according to 'index' benchmark.

        :param prices_m: matrix of prices. Each column represents a stock.
        Each row represents price at successive time stamp
        :return: matrix with betas. Each column represents a stock. Each row
        represents beta at successive time period
        """
        returns_m = ml.divide(ml.subtract(prices_m[1:], prices_m[:-1]),
                              prices_m[:-1])
        index_m = ml.matrix(index).T
        index_returns_m = ml.divide(ml.subtract(index_m[1:], index_m[:-1]),
                                    index_m[:-1])
        result = ml.empty((k, prices_m.shape[1]))
        for i in range(k):
            for j in range(stock_amount):
                x = returns_m[:, j]
                y = index_returns_m[:, i]
                result[i, j] = np.cov(x, y, rowvar=0)[0][1]/np.var(y)
        return result

    def regime(reduced_returns_m):
        """
        Make a regime switch based on PCA standard deviation acceleration.

        :param reduced_returns_m: matrix of PCA. Each column represents a
        stock. Each row represents price at successive time stamp
        :return: one of the strings, 'momentum' - if trend is ment to
        continue its movement, 'mean_reversion' - otherwise
        """
        cross_sect_vol = np.std(reduced_returns_m, axis=1)
        changes = cross_sect_vol[1:] - cross_sect_vol[:-1]
        squared_changes = np.square(changes)

        distance_times = reduced_returns_m.shape[0] - 1  # because there is
                                                         # T - 1 changes
        distance = np.zeros(distance_times)
        for t in range(distance_times):
            sum_amount = min(t + 1, H)
            for i in range(sum_amount):
                distance[t] += squared_changes[t - i, 0]
            distance[t] = np.sqrt(distance[t])
        signal = distance[1:] - distance[:-1]
        if np.max(signal) > 0:
            return 'momentum'
        else:
            return 'mean_reversion'

    prices_m = ml.matrix(prices).T

    # Preparing main matrices for further computations
    log_returns_m = np.log(ml.divide(prices_m[1:], prices_m[:-1]))
    time_period, stock_amount = log_returns_m.shape
    mean_log_returns_m = ml.average(log_returns_m, axis=0)
    demeaned_log_returns_m = log_returns_m - mean_log_returns_m
    covariation_m = demeaned_log_returns_m.T * demeaned_log_returns_m

    # Count eigenvectors of covariation matrix and compose PCA matrix from them
    e_values, e_vectors = eig(covariation_m)
    abs_e_values = np.absolute(e_values)
    # TODO: np.absolute(e_vectors) or something like that
    indexed_abs_e_values = [(i, v) for i, v in enumerate(abs_e_values)]
    w = sorted(indexed_abs_e_values, reverse=False,
               key=lambda x: x[1])
    e_vectors_m = ml.empty((stock_amount, k))
    for j in range(k):
        e_vectors_m[:, j] = e_vectors[:, w[j][0]]

    # Main part: project returns on PCA universe
    reduced_returns_m = (e_vectors_m.T * demeaned_log_returns_m.T).T

    # Count beta parameters with respect to given benchmark index
    betas_m = betas(prices_m)

    time = time_period - time_shift
    if time < H:
        raise WrongParameterException("time_shift should be less than H")

    # Collect data from returns in one vector
    accumulated_reduced_returns = ml.zeros((1, k))
    for i in range(H):
        accumulated_reduced_returns += reduced_returns_m[time - 1 - i]

    # Make a prediction about further returns behaviour
    estimation = accumulated_reduced_returns * betas_m + \
                 mean_log_returns_m

    if regime_switcher:
        regime = regime(reduced_returns_m)
    else:
        regime = 'mean_reversion'

    # Finally, decide for each stock, whether we need to sell it as
    # overvalued or buy as undervalued. Other way around for momentum switch
    max_recent_log_returns = log_returns_m[-H:].max(0)
    result = []
    for i in range(stock_amount):
        if max_recent_log_returns[0, i] > estimation[0, i] + epsilon:
            if regime == 'mean_reversion':
                result.append('sell')
            else:
                result.append('buy')
        elif max_recent_log_returns[0, i] < estimation[0, i] - epsilon:
            if regime == 'mean_reversion':
                result.append('buy')
            else:
                result.append('sell')
        else:
            result.append(None)
    return result


class WrongParameterException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)