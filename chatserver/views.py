# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from ws4redis.redis_store import RedisMessage
from ws4redis.publisher import RedisPublisher
#from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template import RequestContext
from django.shortcuts import render_to_response

from chatserver.models import *
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.core.cache import cache

class BroadcastChatView(TemplateView):
    template_name = 'broadcast_chat.html'

    def get(self, request, *args, **kwargs):
        welcome = RedisMessage('Hello everybody')  # create a welcome message to be sent to everybody
        RedisPublisher(facility='foobar', broadcast=True).publish_message(welcome)
        return super(BroadcastChatView, self).get(request, *args, **kwargs)

class TicTacGame(TemplateView):
    template_name = 'tictac.html'

    def get(self, request, *args, **kwargs):
        game_name = self.kwargs.get('game_name')
        context = RequestContext(request)
        moves = cache.get("game."+game_name)
        variables = {'moves': moves}
        game = (TicTacGameSession.objects.filter(name=game_name) or [None])[0]

        if game is None or (game.user != request.user and game.user2 is not None and game.user2 != request.user) or game.state == "over":
            return HttpResponseRedirect('/room_list/')
        if game.user != request.user and game.user2 is None:
            game.user2 = request.user
            game.state = "playing"
            game.save()

            redis_publisher = RedisPublisher(facility='foobar', users=[game.user])
            message = RedisMessage("start")
            redis_publisher.publish_message(message)
            redis_publisher.publish_message(RedisMessage(""))

            variables['my_turn'] = False
            variables['joined'] = True
            # kela
        elif game.user2 is None:
            variables['my_turn'] = True
            variables['joined'] = False
        else:
            variables['my_turn'] = False
            variables['joined'] = True
        variables['first_player'] = game.user == request.user
        variables['game_name'] = game_name
        # variables['second_player']
        print variables
        return render_to_response('tictac.html', variables, context_instance=context)


class SendMove(TemplateView):
    def post(self, request, *args, **kwargs):
        index = request.POST.get("index", None)
        state = request.POST.get("state", None)
        game_name = request.POST.get("game_name", None)
        user = request.user
        # print "==============", user, index, state
        game = TicTacGameSession.objects.filter(Q(user=user) | Q(user2=user)).filter(name=game_name)[0]
        game.state = state
        game.save()

        moves = cache.get('game.'+game.name)
        moves.append(index)
        cache.set('game.'+game.name, moves)

        other_player = game.user2 if game.user == user else game.user
        redis_publisher = RedisPublisher(facility='foobar', users=[other_player])
        message = RedisMessage(index)
        redis_publisher.publish_message(message)
        # Added an extra blank message, as redis queue was sending the last message after reload
        redis_publisher.publish_message(RedisMessage(''))
        return HttpResponse('Ok')


class GameList(TemplateView):
    template_name = 'game_list.html'

    def get(self, request, *args, **kwargs):
        game = TicTacGameSession.objects.filter(Q(user=request.user) | Q(user2=request.user)).filter(state__in=['open', 'playing'])
        if game.exists():
            return HttpResponseRedirect('/gameroom/' + game[0].name + "/")
        context = RequestContext(request)
        games = TicTacGameSession.objects.filter(state__in=['open', 'playing'])
        variables = {'games': games}
        return render_to_response('game_list.html', variables, context_instance=context)

    @method_decorator(login_required(login_url='/accounts/login/'))
    def dispatch(self, *args, **kwargs):
        return super(GameList, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", None)
        if TicTacGameSession.objects.filter(name=name).exists():
            return HttpResponse('Game with this name already present.')
        c = TicTacGameSession.objects.create(user=request.user, name=name, state='open')
        cache.set("game."+name, [])
        return HttpResponse('/gameroom/' + name + "/")


class Register(TemplateView):
    def post(self, request, *args, **kwargs):
        uf = UserForm(request.POST, prefix='user')
        if uf.is_valid():
            user = uf.save()
            user.set_password(uf.cleaned_data.get("password"))
            user.save()
        return HttpResponseRedirect("/accounts/login/")

    def get(self, request, *args, **kwargs):
        uf = UserForm(prefix='user')
        return render_to_response('registration/register.html', dict(userform=uf),
                                    context_instance=RequestContext(request))