__author__ = 'mosin'
from django.conf.urls import patterns, url
from strategy_runner import views

urlpatterns = patterns('',
                       # ex: /runner/
                       url(r'^$', views.index, name='index'))