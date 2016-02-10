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
        # print "0000000---", game is None, game.user!=request.user, game.user2, game.state
        if game is None or (game.user != request.user and game.user2 is not None and game.user2 != request.user) or game.state == "over":
            # kela
            return HttpResponseRedirect('/room_list/')
        if game.user != request.user and game.user2 is None:
            print "*************************************"
            game.user2 = request.user
            game.state = "playing"
            game.save()
            # game.update(user2=request.user)
            redis_publisher = RedisPublisher(facility='foobar', users=[game.user])
            message = RedisMessage("start")
            redis_publisher.publish_message(message)

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
        # variables['second_player']
        print variables
        return render_to_response('tictac.html', variables, context_instance=context)
        # return super(TicTacGame, self).get(request, *args, **kwargs)


class SendMove(TemplateView):
    def post(self, request, *args, **kwargs):
        index = request.POST.get("index", None)
        state = request.POST.get("state", None)
        user = request.user
        print "==============", user, index, state
        game = TicTacGameSession.objects.filter(Q(user=user) | Q(user2=user))[0]
        game.state = state
        game.save()

        moves = cache.get('game.'+game.name)
        print "------------", moves
        moves.append(index)
        print "------------", moves
        cache.set('game.'+game.name, moves)

        other_player = game.user2 if game.user == user else game.user
        redis_publisher = RedisPublisher(facility='foobar', users=[other_player])
        message = RedisMessage(index)
        redis_publisher.publish_message(message)
        redis_publisher.publish_message(RedisMessage(''))
        return HttpResponse('Ok')




class GameList(TemplateView):
    #login_required = True
    template_name = 'game_list.html'

    def get(self, request, *args, **kwargs):
        game = TicTacGameSession.objects.filter(Q(user=request.user) | Q(user2=request.user)).filter(state__in=['open', 'playing'])
        if game.exists():
            return HttpResponseRedirect('/gameroom/' + game[0].name + "/")
        context = RequestContext(request)
        games = TicTacGameSession.objects.filter(state='open')
        variables = {'games': games}
        print variables
        # return super(GameList, self).get(request, *args, **kwargs)
        return render_to_response('game_list.html', variables, context_instance=context)

    @method_decorator(login_required(login_url='/accounts/login/'))
    def dispatch(self, *args, **kwargs):
        return super(GameList, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", None)
        if TicTacGameSession.objects.filter(name=name).exists():
            return HttpResponse('Game with this name already present.')
        print "*****************", request.user
        # kela
        c = TicTacGameSession.objects.create(user=request.user, name=name, state='open')
        cache.set("game."+name, [])
        return HttpResponse('/gameroom/' + name + "/")
        # return HttpResponseRedirect('/chat/')
        # return super(GameList, self).get(request, *args, **kwargs)


class Register(TemplateView):
    def post(self, request, *args, **kwargs):
        uf = UserForm(request.POST, prefix='user')
        # upf = UserProfileForm(request.POST, prefix='userprofile')
        if uf.is_valid():
            user = uf.save()
            user.set_password(uf.cleaned_data.get("password"))
            user.save()
            # userprofile = upf.save(commit=False)
            # userprofile.user = user
            # userprofile.save()
        return HttpResponseRedirect("/accounts/login/")

    def get(self, request, *args, **kwargs):
        uf = UserForm(prefix='user')
        # upf = UserProfileForm(prefix='userprofile')
        return render_to_response('registration/register.html', dict(userform=uf),
                                    context_instance=RequestContext(request))


# class UserChatView(TemplateView):
#     template_name = 'user_chat.html'

#     def get_context_data(self, **kwargs):
#         context = super(UserChatView, self).get_context_data(**kwargs)
#         context.update(users=User.objects.all())
#         return context

#     @csrf_exempt
#     def dispatch(self, *args, **kwargs):
#         return super(UserChatView, self).dispatch(*args, **kwargs)

#     def post(self, request, *args, **kwargs):
#         redis_publisher = RedisPublisher(facility='foobar', users=[request.POST.get('user')])
#         message = RedisMessage(request.POST.get('message'))
#         redis_publisher.publish_message(message)
#         return HttpResponse('OK')


# class GroupChatView(TemplateView):
#     template_name = 'group_chat.html'

#     def get_context_data(self, **kwargs):
#         context = super(GroupChatView, self).get_context_data(**kwargs)
#         context.update(groups=Group.objects.all())
#         return context

#     @csrf_exempt
#     def dispatch(self, *args, **kwargs):
#         return super(GroupChatView, self).dispatch(*args, **kwargs)

#     def post(self, request, *args, **kwargs):
#         redis_publisher = RedisPublisher(facility='foobar', groups=[request.POST.get('group')])
#         message = RedisMessage(request.POST.get('message'))
#         redis_publisher.publish_message(message)
#         return HttpResponse('OK')
