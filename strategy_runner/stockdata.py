__author__ = 'mosin'

import urllib2
import csv
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


def history_run(stocks, index, chunk_size, start_date, end_date=date.today()):
    # def chunks(l, size):
    #     reminder = len(l) % size
    #     result = []
    #     if reminder:
    #         result.append(l[:reminder])
    #     for i in xrange(reminder, len(l), size):
    #         result.append(l[i:i+size])
    #     return result
    def chunks(l, size):
        result = []
        for i in xrange(0, len(l), size):
            result.append(l[i:i+size])
        return result

    #gather and split price data in equal chunks to feed signal
    index_prices = _get_prices(index, start_date, end_date)
    tail = len(index_prices) % chunk_size
    index_prices = chunks(index_prices[tail:], chunk_size)

    #split stock data in the same way
    all_prices = []
    for stock in stocks:
        history = _get_prices(stock, start_date, end_date)

        #define position to be a starting history point. It should be shifted,
        # because k preceding index price time periods are required for the
        # first stock price time period
        start_position = tail + (pca.k - 1) * chunk_size
        all_prices.append(chunks(history[start_position:], chunk_size))

    # amount of time periods
    period_amount = len(all_prices[0])
    result = []
    for i in range(period_amount):
        prices = []
        for stock_price_list in all_prices:
            prices.append(stock_price_list[i])
        result.append(pca.signal(prices, index_prices[i:i + pca.k]))
    return result


# def get_cumulative_returns():
