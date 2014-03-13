__author__ = 'mosin'
from django.test import TestCase
from django.conf import settings
from random import randrange
from datetime import date
import os
import pca
import stockdata


class BasicLogicTests(TestCase):
    def __init__(self):
        TestCase.__init__(self)
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

    def test_history_run_data_fetching(self):
        #parameters:
        pca.k = 2
        pca.H = 4
        pca.regime_switcher = False
        amount = 5
        stocks = stockdata.get_stock_names(self.nasdaq_path, amount)
        index = '^GSPC'
        chunk_size = 9
        start_date = date(2014, 1, 11)
        end_date = date(2014, 3, 11)
        results = stockdata.history_run(stocks, index, chunk_size, start_date,
                                        end_date)
        print results
        print len(results)
        #TODO: assert equal results, [['buy', 'buy', 'buy'], ['buy', 'buy', 'sell'], ['sell', 'sell', 'buy']]

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
    tests.simple_test_random_values()
    tests.test_get_stock_names_5_from_1()
    tests.test_get_stock_names_10_from_27()
    tests.test_history_run_data_fetching()
    #tests.test_history_run_lots_of_parameters()
