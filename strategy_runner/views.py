from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


def index(request):
    #return render(request, 'strategy_runner/index.html')
    return HttpResponseRedirect(reverse("strategy_runner:history"))


def history(request):
    return render(request, 'strategy_runner/base_history.html')


def run(request):
    pass
#    return render(request, 'strategy_runner/index.html')


def scheduler(request):
    return render(request, 'strategy_runner/base_scheduler.html')