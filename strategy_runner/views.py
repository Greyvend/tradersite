from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from datetime import datetime
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
    # try:
    #
    # except: # first look what exceptions can be there
    #     # Redisplay the poll voting form.
    #     return render(request, 'polls/detail.html', {
    #         'poll': p,
    #         'error_message': "You didn't select a choice.",
    #         })
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
    except KeyError:
        raise
    return HttpResponseRedirect(reverse('strategy_runner:history'))
    #return HttpResponse(dates, prices, signals)


def example(request):
    return render(request, 'strategy_runner/example.html')