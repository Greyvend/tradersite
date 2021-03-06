from collections import namedtuple
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from datetime import datetime
from GChartWrapper import Line
import re
import os


import pca
import stockdata


def index(request):
    #return render(request, 'strategy_runner/index.html')
    return HttpResponseRedirect(reverse("strategy_runner:history"))


def history(request):
    return render(request, 'strategy_runner/base_history.html')


def scheduler(request):
    return render(request, 'strategy_runner/base_scheduler.html')


def run(request):
    def graph_img(x, y, name):
        def y_precise():
            result = ["chd=t:"]
            for elem in y:
                result.append(str(elem))
                result.append(',')
            result[-1] = '&'
            return ''.join(result)

        G = Line(y, encoding='text')
        G.axes.type('xy')
        min_y = min(y)
        max_y = max(y)
        G.axes.range(1, min_y, max_y)
        G.scale(min_y, max_y)
        G.axes.label(0, x[0], x[-1])
        G.axes.label(1, min_y, max_y)
        G.title(name)
        image_code = G.img()
        norm_img = re.sub(r'chd=t.*?\&', y_precise(), image_code)
        if len(norm_img) > 2000:
            if len(image_code) > 2000:
                raise LongPeriodException()
            else:
                return image_code
        return norm_img
    try:
        # getting parameters
        start_date = datetime.strptime(request.POST['start_date'],
                                       '%Y-%m-%d').date()
        end_date = datetime.strptime(request.POST['end_date'],
                                     '%Y-%m-%d').date()
        stock_amount = int(request.POST['stock_amount'])
        time_period = int(request.POST['time_period'])
        k = int(request.POST['k'])
        H = int(request.POST['H'])
        regime_switcher = request.POST['regime_switcher']
    except KeyError:
        raise
    # starting our job
    pca.k = k
    pca.H = H
    if regime_switcher == 'off':
        pca.regime_switcher = False
    else:
        pca.regime_switcher = True
    index = '^GSPC'
    source = os.path.join(settings.BASE_DIR,
                          'strategy_runner/stock_names/'
                          'NASDAQ.csv')
    stocks = stockdata.get_stock_names(source, stock_amount)
    try:
        dates, prices, signals = stockdata.history_run(stocks, index,
                                                       time_period, start_date,
                                                       end_date)
    except (pca.WrongParameterException, pca.WrongPricesError) as e:
        return render(request, 'strategy_runner/base_history.html',
                      {'error_message': str(e)})
    date_strings = [date.strftime('%Y-%m-%d') for date in dates]
    returns, pl = stockdata.get_returns_and_pl(prices, signals)

    #prepare img tags with graphs to pass to the template
    graph_imgs = []
    try:
        for i, price_list in enumerate(prices):
            graph_imgs.append(graph_img(date_strings, price_list, stocks[i]))
        graph_imgs.append(graph_img(date_strings, returns,
                                    'Cumulative Log Returns'))
        graph_imgs.append(graph_img(date_strings, pl, r'Profit/Loss'))
    except LongPeriodException as e:
        return render(request, 'strategy_runner/base_history.html',
                      {'error_message': str(e)})

    # NamedPrices = namedtuple('NamedPrices', ['stock', 'prices'])
    # named_prices = []
    # for i, stock in enumerate(stocks):
    #     named_prices.append(NamedPrices(stock, prices[i]))
    return render(request,
                  'strategy_runner/base_history.html',
                  {'graph_imgs': graph_imgs})


class LongPeriodException(Exception):
    def __str__(self):
        return "The chosen period is too long to form a graph"