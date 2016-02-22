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
from django import forms
from django.shortcuts import render

import requests






xml = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
 <soap:Body>
 <UploadStudentAttendance xmlns="https://tempuri.org/">
 <UserName>dasaipokhra</UserName>
 <Password>12345</Password>
 <Studentid>885595</Studentid>
 <Punchdate>2016-02-20</Punchdate>
 <Punchtime>10:59:00</Punchtime>
 <Courseid>1424</Courseid>
 <Batchid>32895</Batchid>
 <Tcid>8474</Tcid>
 <Field1></Field1>
 <Field2></Field2>
 </UploadStudentAttendance>
 </soap:Body>
</soap:Envelope>'''

target_url =  'http://isds-textiles.in/webcon/list.asmx?WSDL'

import csv

class UploadFileForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(max_length=50)
    batchid = forms.CharField(max_length=50)
    courseid = forms.CharField(max_length=50)
    tcid = forms.CharField(max_length=50)
    file = forms.FileField()

class ISDSView(TemplateView):
    
    def get(self, request, *args, **kwargs):
        form = UploadFileForm()
        return render(request, 'isds.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadFileForm(request.POST, request.FILES)
        success = False
        print "******", request.FILES
        if form.is_valid():
            self.handle_uploaded_file(request.FILES['file'])
            success = True
            print "--------"
            students_list = self.read_csv()
            for i in range(1, len(students_list)):
                xml = '''<?xml version="1.0" encoding="utf-8"?>
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                 <soap:Body>
                 <UploadStudentAttendance xmlns="https://tempuri.org/">
                 <UserName>''' + form.cleaned_data.get('username') + '''</UserName>
                 <Password>''' + form.cleaned_data.get('password') + '''</Password>
                 <Studentid>'''+ students_list[i][0]+'''</Studentid>
                 <Punchdate>'''+ students_list[i][1]+'''</Punchdate>
                 <Punchtime>'''+ students_list[i][2]+'''</Punchtime>
                 <Courseid>''' + form.cleaned_data.get('courseid') + '''</Courseid>
                 <Batchid>''' + form.cleaned_data.get('batchid') + '''</Batchid>
                 <Tcid>''' + form.cleaned_data.get('tcid') + '''</Tcid>
                 <Field1></Field1>
                 <Field2></Field2>
                 </UploadStudentAttendance>
                 </soap:Body>
                </soap:Envelope>'''
                headers = {'Content-Type': 'text/xml','charset':'utf-8'}
                r = requests.post(target_url,data=xml,headers=headers, auth=('dasaipokhra','12345'))
                # print 'r.text = ', r.text
                print 'r.content = ', r.content
                print 'r.status_code = ', r.status_code
        return render(request, 'isds.html', {'form': form, 'success': success})
        

    def handle_uploaded_file(self, f):
        with open('isds.txt', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    def read_csv(self):
        # your_list = 
        with open('isds.txt', 'rb') as f:
            reader = csv.reader(f)
            your_list = list(reader)
        return your_list



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