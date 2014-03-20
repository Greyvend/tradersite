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
            result = []
            result.append("chd=t:")
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
        # x_label = [x[i] for i in range(0, len(x), len(x)/10)]
        # y_label = [y[i] for i in range(0, len(y), len(y)/10)]
        G.axes.label(0, x[0], x[-1])
        G.axes.label(1, min_y, max_y)
        G.title(name)
        image_code = G.img()
        norm_img = re.sub(r'chd=t.*?\&', y_precise(), image_code)
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
    dates, prices, signals = stockdata.history_run(stocks, index,
                                                   time_period, start_date,
                                                   end_date)
    date_strings = [date.strftime('%Y-%m-%d') for date in dates]
    returns, pl = stockdata.get_returns_and_pl(prices, signals)

    #prepare img tags with graphs to pass to the template
    graph_imgs = []
    for i, price_list in enumerate(prices):
        graph_imgs.append(graph_img(date_strings, price_list, stocks[i]))
    graph_imgs.append(graph_img(date_strings, returns,
                                'Cumulative Log Returns'))
    graph_imgs.append(graph_img(date_strings, pl, r'Profit/Loss'))

    # NamedPrices = namedtuple('NamedPrices', ['stock', 'prices'])
    # named_prices = []
    # for i, stock in enumerate(stocks):
    #     named_prices.append(NamedPrices(stock, prices[i]))
    return render(request,
                  'strategy_runner/base_history.html',
                  {'graph_imgs': graph_imgs})


def example(request):
    return render(request, 'strategy_runner/example.html')

import random
from django.http import HttpResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter


def simple(request):
    fig = Figure()
    ax = fig.add_subplot(111)
    x = []
    y = []
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now += delta
        y.append(random.randint(0, 1000))
    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response