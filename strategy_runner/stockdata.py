__author__ = 'mosin'
import urllib2
import csv
import numpy as np
from datetime import date, datetime
import pca


def _get_prices(stock, start_date, end_date):
    # Use URL template and fill in stock symbol, start date and end date
    """
    Get dates and prices on that dates.

    :param stock: name of stock to get data about
    :param start_date: starting date
    :param end_date: last date
    :return: list of tuples (date, price)
    """
    url = "http://ichart.finance.yahoo.com/table.csv?s={0}&a={1}&b={2}&c={3}" \
          "&d={4}&e={5}&f={6}&g=d&ignore=.csv" \
        .format(urllib2.quote(stock), start_date.month - 1, start_date.day,
                start_date.year, end_date.month - 1, end_date.day, end_date
            .year)

    # Download the data using the URL crafted above
    data = urllib2.urlopen(url).read()

    # Split it based on new line characters
    lines = data.split('\n')

    dates = []  # Dates will hold dates on which prices are presented
    closing_prices = []  # Closing prices will hold the adjusted close for each
                         # day
    # Loop through each line (meaning each timestamp)
    for line in reversed(lines[1:]):
        # Split CSV data
        items = line.split(',')

        # Verify that the results have 7 items
        if len(items) == 7:
            # Add the first item in the list, which is the date after
            # converting it using the following pattern
            dates.append(datetime.strptime(items[0], '%Y-%m-%d').date())
            # Add the last item in the list, which will be the adjusted close
            # price, after converting it to a float
            closing_prices.append(float(items[6]))
    return dates, closing_prices


def get_stock_names(source, amount, start=1):
    """
    Fetch stock names from csv file.

    :param source: csv file to be searched for names
    :param amount: amount of stock names to get
    :param start: first index to start fetching from
    :return: list of strings, representing stock names
    """
    result = []
    with open(source, buffering=1) as f:
        row_no = 0
        for row in csv.reader(f, delimiter=','):
            if row_no - start == amount:
                break
            if row_no >= start:
                result.append(row[0])
            row_no += 1
    return result


def history_run(stocks, index, time_period, start_date, end_date=date.today()):
    """
    Run PCA signal on desired history period with particular stocks and
    benchmark index
    :param stocks: list of stock names to run strategy on
    :param index: name of benchmark index to compare risks with
    :param time_period: size of time period, for which prices will be given
    to signal function
    :param start_date: beginning date to run from.
    Important note: Some time from the beginning of this period is required for
    the statistic gathering, so signal will be run with some lag from
    start_date
    :param end_date: final date to run signal on
    :return: trinity of: dates - list of dates on which signal was run,
    prices - list of lists of corresponding prices for all the stocks,
    signals - list of signal results. Every of those is a list too.
    """

    def backward_chunks(l, amount, size, pos):
        result = []
        for i in range((pos - size * amount), pos, size):
            result.append(l[i:i+size])
        return result

    #gather and split price data in equal chunks to feed signal
    dates, index_prices = _get_prices(index, start_date, end_date)

    #split stock data in the same way
    all_prices = []

    # define position to be a starting history point. It should be shifted,
    # because k preceding index price time periods are required for the
    # first stock price time period
    start_position = (pca.k - 1) * time_period
    for stock in stocks:
        history = _get_prices(stock, start_date, end_date)[1][start_position:]
        all_prices.append(history)

    # make successive calls to signal function with continuous time history
    signals = []
    stop_pos = len(all_prices[0]) + 1
    for t in range(time_period, stop_pos):
        # select prices of certain time period
        prices = []
        for stock_price_list in all_prices:
            prices.append(stock_price_list[t - time_period:t])

        # divide index list to chunks of length k, according to algorithm
        # requirements
        split_index = backward_chunks(index_prices, pca.k, time_period,
                                      t + start_position)

        # call algorithm function
        try:
            signals.append(pca.signal(prices, split_index))
        except pca.WrongPricesError, pca.WrongParameterException:
            raise


    # leave only prices that correspond signals
    prices = [price_list[time_period - 1:] for price_list in all_prices]
    # leave only dates that correspond signals
    dates = dates[start_position + time_period - 1:]
    return dates, prices, signals


def get_returns_and_pl(all_prices, signals):
    def get_log_returns(open_prices, cur_prices):
        """
        Count logarithmic returns for both long and short open positions,
        as average of all of the returns of the stocks in portfolio.

        :param open_prices: list of prices on which positions were opened
        :param cur_prices: list of current prices to compare with
        :return: average return percentage
        :rtype : float
        """
        gross_returns = []
        for i, price in enumerate(open_prices):
            if price and price > 0:
                # long position gross return
                gross_returns.append(price/cur_prices[i])
            elif price and price < 0:
                price *= -1
                # short position gross return
                gross_returns.append((2 * price - cur_prices[i])/price)
        return np.log(np.mean(gross_returns))

    def refresh_prices(open_prices, cur_prices, signal_number):
        """
        Close positions and open new ones depending on signals[signal_number]
        data.

        :type open_prices: list
        :param open_prices: list of current open open_prices for all stocks, negative
        open_prices mean short positions
        :param signal_number: index of signal to renew positions from
        :return : P&L of closed trades
        """
        profit_loss = 0
        cur_signal = signals[signal_number]
        for i, cur_price in enumerate(cur_prices):
            if cur_signal[i] == 'buy':
                if not open_prices[i]:
                    open_prices[i] = cur_price
                elif open_prices[i] < 0:  # it means short position, we should
                # close it
                    profit_loss += -open_prices[i] - cur_price
                    open_prices[i] = None
            elif cur_signal[i] == 'sell':
                if not open_prices[i]:
                    open_prices[i] = -cur_price
                elif open_prices[i] > 0:  # it means long position, we should
                # close it
                    profit_loss += cur_price - open_prices[i]
                    open_prices[i] = None
        return profit_loss

    open_prices = [None] * len(all_prices)

    # go through all signals and count log returns and collect P&Ls
    returns = [0]
    profit_loss = [0]
    for i, signal in enumerate(signals):
        cur_prices = [stock_price_list[i] for stock_price_list in all_prices]
        if i == 0:
            refresh_prices(open_prices, cur_prices, 0)
            continue

        # accumulate recent log returns        
        returns.append(returns[i - 1] + get_log_returns(open_prices,
                                                        cur_prices))

        # refresh open_prices after signal work
        new_pl = refresh_prices(open_prices, cur_prices, i)

        # accumulate pl from last closed trades
        profit_loss.append(profit_loss[i - 1] + new_pl)
    return returns, profit_loss


# class StockDataException(Exception):
#     pass
#
#
# class ShortStockHistory(StockDataException):
#     def __init__(self, stock, begin_date):
#         self.stock = stock
#         self.begin_date = begin_date
#
#     def __str__(self):
#         return "History data for stock ", repr(self.stock), " exists only ",\
#                "from ", repr(self.begin_date)
#
#
# class ShortHistoryChosen(StockDataException):
#     def __init__(self, timestamps):
#         self.timestamps = timestamps
#
#     def __str__(self):
#         return "History data lacks ", repr(self.timestamps), " timestamps ",\
#         "to collect statisctic. Please, choose larger analysis period or ",\
#         "lessen either the PCA dimesion parameter or Time period."