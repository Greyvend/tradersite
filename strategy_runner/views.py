from django.shortcuts import render


def index(request):
    return render(request, 'strategy_runner/index.html')
