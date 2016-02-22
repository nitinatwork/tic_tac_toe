# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns, include
from django.core.urlresolvers import reverse_lazy
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from .views import BroadcastChatView, TicTacGame, GameList, SendMove, Register, ISDSView
admin.autodiscover()


urlpatterns = patterns('',
	url(r'^isds/$', ISDSView.as_view(), name='isds'),
    url(r'^chat/$', BroadcastChatView.as_view(), name='broadcast_chat'),
    url(r'^room_list/$', GameList.as_view(), name='room_list'),
    url(r'^gameroom/(?P<game_name>[-\w]+)/$', TicTacGame.as_view(), name='game_room'),
    url(r'^send_move/$', SendMove.as_view(), name='send_move'),
    url(r'^register/$', Register.as_view(), name='register'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^.*$', RedirectView.as_view(url=reverse_lazy('room_list'))),
    # url(r'^$', RedirectView.as_view(url=reverse_lazy('room_list'))),
) + staticfiles_urlpatterns()
