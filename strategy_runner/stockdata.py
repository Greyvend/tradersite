__author__ = 'mosin'
import urllib2
import csv
import numpy as np
from datetime import date
import pca


def _get_prices(stock, start_date, end_date):
    # Use URL template and fill in stock symbol, start date and end date
    url = "http://ichart.finance.yahoo.com/table.csv?s={0}&a={1}&b={2}&c={3}" \
          "&d={4}&e={5}&f={6}&g=d&ignore=.csv" \
        .format(urllib2.quote(stock), start_date.month - 1, start_date.day,
                start_date.year, end_date.month, end_date.day, end_date.year)

    # Download the data using the URL crafted above
    data = urllib2.urlopen(url).read()

    # Split it based on new line characters
    lines = data.split('\n')

    # Closing prices will hold the adjusted close for each day
    closing_prices = []

    # Loop through each line (meaning each day)
    for line in lines[1:]:

        # Split CSV data
        items = line.split(',')

        # Verify that the results have 7 items
        if len(items) == 7:
            # Add the last item in the list, which will be the adjusted close
            # price, after converting it to a float
            closing_prices.append(float(items[6]))
    # Return the results
    return closing_prices


def get_stock_names(name, amount, start=1):
    result = []
    with open(name, buffering=1) as f:
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

    :param stocks:
    :param index:
    :param time_period:
    :param start_date:
    :param end_date:
    :return:
    """

    def backward_chunks(l, amount, size, pos):
        result = []
        for i in range((pos - size * amount), pos, size):
            result.append(l[i:i+size])
        return result

    #gather and split price data in equal chunks to feed signal
    index_prices = _get_prices(index, start_date, end_date)

    #split stock data in the same way
    all_prices = []
    start_position = (pca.k - 1) * time_period
    for stock in stocks:
        # define position to be a starting history point. It should be shifted,
        # because k preceding index price time periods are required for the
        # first stock price time period
        history = _get_prices(stock, start_date, end_date)[start_position:]
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
        signals.append(pca.signal(prices, split_index))

    # get cumulative returns for all of the timestamps
    return signals


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
            if price > 0:
                # long position gross return
                gross_returns.append(price/cur_prices[i])
            elif price < 0:
                price *= -1
                # short position gross return
                gross_returns.append((2 * price - cur_prices[i])/cur_prices[i])
        return np.log(np.mean(gross_returns))

    def refresh_prices(prices, signal_number):
        """
        Close positions and open new ones depending on signals[signal_number]
        data.

        :type prices: list
        :param prices: list of current open prices for all stocks, negative
        prices mean short positions
        :param signal_number: index of signal to renew positions from
        :return : P&L of closed trades
        """
        profit_loss = 0
        cur_signal = signals[signal_number]
        for i in range(all_prices):
            if cur_signal[i] == 'buy':
                if not prices[i]:
                    prices[i] = all_prices[i][signal_number]
                elif prices[i] < 0:  # it means short position, we should
                # close it
                    profit_loss = -prices[i] - cur_signal[i]
                    prices[i] = None
            elif cur_signal[i] == 'sell':
                if not prices[i]:
                    prices[i] = -all_prices[i][signal_number]
                elif prices[i] > 0:  # it means long position, we should
                # close it
                    profit_loss = -prices[i] - cur_signal[i]
                    prices[i] = None
        return profit_loss

    open_prices = [None] * len(all_prices)

    # fill open_prices with initial stock prices data
    refresh_prices(open_prices, 0)

    # go through all signals and count log returns and collect P&Ls
    returns = [0]
    profit_loss = []
    for i, signal in signals[1:]:
        # accumulate recent log returns
        cur_prices = [stock_price_list[i] for stock_price_list in all_prices]
        returns.append(returns[i - 1] + get_log_returns(open_prices,
                                                        cur_prices))

        # refresh open_prices after signal work
        new_pl = refresh_prices(open_prices, i)

        # append pl from last closed trades
        profit_loss.append(new_pl)
    return returns, profit_loss


