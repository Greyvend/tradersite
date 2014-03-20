__author__ = 'mosin'
from django.test import TestCase
from django.conf import settings
from random import randrange
import datetime
import os
import pca
import stockdata


class BasicLogicTests(TestCase):
    def __init__(self, *args, **kwargs):
        super(BasicLogicTests, self).__init__(*args, **kwargs)
        self.nasdaq_path = os.path.join(settings.BASE_DIR,
                                        'strategy_runner/stock_names/'
                                        'NASDAQ.csv')

    def runTest(self):
        pass

    def simple_test_random_values(self):
        #parameters
        pca.k = 2
        pca.H = 2
        prices = [[1.0, 1.1, 1.2, 1.3], [2.0, 2.1, 2.2, 2.3], [3.0, 3.1, 3.2,
                                                               3.3]]
        index = [[randrange(1, 20) for j in range(4)] for i in range(pca.k)]
        results = pca.signal(prices, index)
        self.assertEqual(results, ['sell', 'sell', 'sell'])

    def test_get_stock_names_5_from_1(self):
        amount = 5

        first_5_nasdaq_stocks = stockdata.get_stock_names(self.nasdaq_path,
                                                          amount)
        self.assertEqual(first_5_nasdaq_stocks,
                         ['FLWS', 'FCTY', 'FCCY', 'SRCE', 'FUBC'])

    def test_get_stock_names_10_from_27(self):
        amount = 10
        start = 27
        path = 'stock_names/NASDAQ.csv'
        first_10_nasdaq_stocks = stockdata.get_stock_names(self.nasdaq_path,
                                                           amount, start)
        right_stocks = ['ACET', 'ACHN', 'ACIW', 'ACNB', 'ACOR',
                'ACFN', 'ACTS', 'ACPW', 'ATVI', 'BIRT']
        self.assertEqual(first_10_nasdaq_stocks, right_stocks)

    def test_history_run_simple(self):
        # parameters:
        pca.k = 2
        pca.H = 4
        stocks = ['GOOG', 'YHOO']
        index = '^GSPC'
        time_period = 10
        start_date = datetime.date(2014, 2, 11)
        end_date = datetime.date(2014, 3, 18)

        # run tested function
        dates, prices, signals = stockdata.history_run(stocks, index,
                                                       time_period, start_date,
                                                       end_date)

        # correct values
        right_signals = [['sell', 'sell', 'sell', 'sell', 'sell'],
                         ['sell', 'sell', 'sell', 'sell', 'sell'],
                         ['buy', 'sell', 'sell', 'buy', 'buy'],
                         ['buy', 'sell', 'sell', 'sell', 'buy'],
                         ['sell', 'sell', 'sell', 'sell', 'sell']]
        right_dates = [datetime.date(2014, 3, 7),
                       datetime.date(2014, 3, 10),
                       datetime.date(2014, 3, 11),
                       datetime.date(2014, 3, 12),
                       datetime.date(2014, 3, 13)]
        right_prices = [[5.41, 5.46, 5.47, 5.46, 5.36],
                        [8.11, 8.13, 8.0, 7.89, 7.97],
                        [10.25, 10.3, 10.25, 10.25, 10.3],
                        [32.12, 32.01, 31.67, 31.94, 31.81],
                        [7.87, 7.9, 7.81, 7.79, 7.64]]

        # checking equality
        print dates
        print prices
        print signals
        # self.assertEqual(dates, right_dates)
        # self.assertEqual(prices, right_prices)
        # self.assertEqual(signals, right_signals)

    def test_history_run_data_fetching(self):
        #parameters:
        pca.k = 2
        pca.H = 4
        pca.regime_switcher = False
        amount = 5
        stocks = stockdata.get_stock_names(self.nasdaq_path, amount)
        index = '^GSPC'
        time_period = 9
        start_date = datetime.date(2014, 2, 11)
        end_date = datetime.date(2014, 3, 13)
        dates, prices, signals = stockdata.history_run(stocks, index,
                                                       time_period, start_date,
                                                       end_date)
        right_signals = [['sell', 'sell', 'sell', 'sell', 'sell'],
                         ['sell', 'sell', 'sell', 'sell', 'sell'],
                         ['buy', 'sell', 'sell', 'buy', 'buy'],
                         ['buy', 'sell', 'sell', 'sell', 'buy'],
                         ['sell', 'sell', 'sell', 'sell', 'sell']]
        right_dates = [datetime.date(2014, 3, 7),
                       datetime.date(2014, 3, 10),
                       datetime.date(2014, 3, 11),
                       datetime.date(2014, 3, 12),
                       datetime.date(2014, 3, 13)]
        right_prices = [[5.41, 5.46, 5.47, 5.46, 5.36],
                        [8.11, 8.13, 8.0, 7.89, 7.97],
                        [10.25, 10.3, 10.25, 10.25, 10.3],
                        [32.12, 32.01, 31.67, 31.94, 31.81],
                        [7.87, 7.9, 7.81, 7.79, 7.64]]
        self.assertEqual(dates, right_dates)
        self.assertEqual(prices, right_prices)
        self.assertEqual(signals, right_signals)

    def test_history_run_big_data(self):
        """
        start_date	      u'2010-01-05'
        end_date          u'2014-03-20'
        H	              u'10'
        k	              u'5'
        regime_switcher   u'off'
        stock_amount	  u'10'
        time_period	      u'20'
        """
        pass

    def test_get_returns_and_pl_average_return(self):
        """
        Run on simple 2 period time schema and verify that average return is
        being processed correctly. No positions are closed.
        """
        all_prices = [[1., 2.], [3., 4.], [5., 6.]]
        signals = [['buy', 'buy', 'sell'],
                   [None, None, None]]
        returns, p_and_l = stockdata.get_returns_and_pl(all_prices, signals)
        self.assertEqual(returns, [0, -0.38077249551779302])
        self.assertEqual(p_and_l, [0, 0])

    def test_get_returns_and_pl_closing_trades(self):
        """
        Run on simple 2 period time schema and verify that trades are closed
        and P&L is counted correctly.
        """
        all_prices = [[1., 2.], [3., 4.], [5., 6.]]
        signals = [['buy', 'buy', 'sell'],
                   ['sell', 'sell', 'buy']]
        returns, p_and_l = stockdata.get_returns_and_pl(all_prices, signals)
        self.assertEqual(returns, [0, -0.38077249551779302])
        self.assertEqual(p_and_l, [0, 1.0])

    def test_get_returns_and_pl_3_days_range(self):
        """
        Run on 2 period time schema and verify that double 'buy' doesn't
        produce any changes. After closing long position another 'sell' is
        made on day 3.
        """
        all_prices = [[1., 2., 2.6, 2.9], [3., 4., 4.4, 4.9], [5., 6., 7.13,
                                                            7.18]]
        signals = [['buy', 'buy', 'sell'],
                   ['sell', 'buy', 'buy'],
                   ['sell', None, 'sell'],
                   ['buy', None, 'buy']]
        returns, p_and_l = stockdata.get_returns_and_pl(all_prices, signals)
        self.assertEqual(returns, [0, -0.38077249551779302,
                                   -0.76376474777389891, -0.95015550861867115])
        self.assertEqual(p_and_l, [0, 0.0, 0.0, -0.34999999999999964])


    # def test_history_run_lots_of_parameters(self):
    #     stocks = ['GOOG', 'YHOO', 'PLUG']
    #     index = '^GSPC'
    #     pca.regime_switcher = False
    #     start_date = date(2013, 3, 11)
    #     end_date = date(2014, 3, 11)
    #     for k_test in range(10):
    #         for h_test in range(20):
    #             for chunk_size_test in range(1, 3 * h_test):
    #                 pca.k = k_test
    #                 pca.H = h_test
    #                 chunk_size = chunk_size_test
    #                 results = stockdata.history_run(stocks, index, chunk_size,
    #                                                 start_date, end_date)
    #                 print results
    #
    #     index = '^GSPC'
    #     chunk_size = 9
    #     start_date = date(2014, 1, 11)
    #     end_date = date(2014, 3, 11)
    #     results = stockdata.history_run(stocks, index, chunk_size, start_date,
    #                                     end_date)
    #     # results = stockdata.history_run(stocks, index, chunk_size)
    #     print results
    #     #TODO: assert equal results, [['buy', 'buy', 'buy'], ['buy', 'buy', 'sell'], ['sell', 'sell', 'buy']]

if __name__ == '__main__':
    tests = BasicLogicTests()
    # tests.simple_test_random_values()
    # tests.test_get_stock_names_5_from_1()
    # tests.test_get_stock_names_10_from_27()
    tests.test_history_run_simple()
    # tests.test_history_run_data_fetching()
    # tests.test_get_returns_and_pl_average_return()
    # tests.test_get_returns_and_pl_closing_trades()
    # tests.test_get_returns_and_pl_3_days_range()

