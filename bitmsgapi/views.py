from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django import forms
from bitmsgapi.models import OutMessage, Address, Identity, Message
import xmlrpclib
import json
import datetime

_API = "http://bitmessage:password@localhost:8444"

class SendForm(forms.Form):
    sender = forms.ModelChoiceField(queryset=Identity.objects.all())
    subject = forms.CharField(max_length=200)
    message = forms.CharField(max_length=50000, widget=forms.Textarea(attrs={'rows':20, 'cols':100}))

class NewAddress(forms.Form):
    label = forms.CharField(max_length=100)

class SubscribeForm(forms.Form):
    label = forms.CharField(max_length=100)
    address = forms.CharField(max_length=100)

class JoinChan(forms.Form):
    address = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)

def update_ids():
    api = xmlrpclib.ServerProxy(_API)
    jsonids = json.loads(api.listAddresses())
    ids = jsonids['addresses']
    num_ids = len(ids)
    
    if num_ids == 0:
        return

    for i in range(0, num_ids):
        ident = ids[i]
        found = Identity.objects.filter(address=ident['address'])
        if len(found) == 0:
            new_id = Identity.objects.create(address=ident['address'], label=ident['label'])
            new_id.save()
    return

def update_msgs():
    api = xmlrpclib.ServerProxy(_API)
    new_msgs = json.loads(api.getAllInboxMessages())
    num_msgs = len(new_msgs['inboxMessages'])
    if num_msgs == 0:
        return
    for m in range (0, num_msgs):
        message = new_msgs['inboxMessages'][m]
        new_m = Message()
        i = Identity.objects.filter(address=message['toAddress'])
        if len(i) != 0:
            new_m.msg_to = i[0]
        else:
            i = Identity.objects.create(address=message['toAddress'], label='default')
            i.save()
            new_m.msg_to = i
        a = Address.objects.filter(address=message['fromAddress'])
        if len(a) != 0:
            new_m.msg_from = a[0]
        else:
            a = Address.objects.create(address=message['fromAddress'], label='default')
            a.save()
            new_m.msg_from = a
        new_m.subject = message['subject'].decode('base64')
        new_m.rcv_date = datetime.datetime.fromtimestamp(int(message['receivedTime']))
        new_m.msg = message['message'].decode('base64')
        new_m.save()
        api.trashMessage(message['msgid'])
    return

def update_sent():
    api = xmlrpclib.ServerProxy(_API)
    sent_msgs = json.loads(api.getAllSentMessages())
    num_msgs = len(sent_msgs['sentMessages'])
    sending = False
    if num_msgs == 0:
        return
    for m in range(0, num_msgs):
        message = sent_msgs['sentMessages'][m]
        if message['msgid'] == "":
            sending = True
        sm = OutMessage.objects.filter(msg_id=message['msgid'])
        if len(sm) != 0:
            update_msg = sm[0]
            update_msg.last_action_date = datetime.datetime.fromtimestamp(int(message['lastActionTime']))
            update_msg.msg_status = message['status']
            update_msg.save()
        else:
            new_om = OutMessage()
            a = Address.objects.filter(address=message['toAddress'])
            if len(a) != 0:
                new_om.msg_to = a[0]
            else:
                a = Address.objects.create(address=message['toAddress'], label='default')
                a.save()
                new_om.msg_to = a
            i = Identity.objects.filter(address=message['fromAddress'])
            if len(i) != 0:
                new_om.msg_from = i[0]
            else:
                i = Identity.objects.create(address=message['fromAddress'], label='default')
                i.save()
                new_om.msg_from = i
            new_om.subject = message['subject'].decode('base64')
            new_om.last_action_date = datetime.datetime.fromtimestamp(int(message['lastActionTime']))
            new_om.msg = message['message'].decode('base64')
            new_om.msg_status = message['status']
            new_om.msg_id = message['msgid']
            new_om.save()
    if not sending:
        for o in OutMessage.objects.filter(msg_id=""):
            o.delete()
    return

def index(request):
    return HttpResponse("bitmsg index page not implemented yet")

def msg(request, msg_id):
    update_msgs()
    msg = get_object_or_404(Message, pk=msg_id)
    msg.msg_unread = False
    msg.save()
    template = loader.get_template('bitmsgapi/msg.html')
    context = {'msg': msg}
    return render(request, 'bitmsgapi/msg.html', context)

def omsg(request, msg_id):
    update_sent()
    msg = get_object_or_404(OutMessage, pk=msg_id)
    template = loader.get_template('bitmsgapi/msg.html')
    context = {'msg': msg}
    return render(request, 'bitmsgapi/omsg.html', context)

def inbox(request):
    #TODO add ability to delete messages
    update_msgs()
    msgs = Message.objects.all()
    template = loader.get_template('bitmsgapi/inbox.html')
    context = {'msgs': msgs}
    return render(request, 'bitmsgapi/inbox.html', context)

def addressbook(request):
    api = xmlrpclib.ServerProxy(_API)
    sub = json.loads(api.listSubscriptions())
    addrs = Address.objects.all()
    subs = []
    for s in sub['subscriptions']:
        subs.append({'address':s['address'],'label':s['label'].decode('base64')})
    template = loader.get_template('bitmsgapi/addressbook.html')
    context = {'addrs': addrs, 'subs': subs}
    return render(request, 'bitmsgapi/addressbook.html', context)

def del_addr(request, address):
    addr = Address.objects.filter(address=address)
    if len(addr) != 0:
        addr[0].delete()
    return HttpResponseRedirect('/addressbook')

def identities(request):
    update_ids()
    ids = Identity.objects.all()
    template = loader.get_template('bitmsgapi/identities.html')
    context = {'ids': ids}
    return render(request, 'bitmsgapi/identities.html', context)

def outbox(request):
    #TODO add ability to delete out messages
    update_sent()
    msgs = OutMessage.objects.all()
    template = loader.get_template('bitmsgapi/outbox.html')
    context = {'msgs' : msgs}
    return render(request, 'bitmsgapi/outbox.html', context)

def send(request, address="", faddr=""):
    api = xmlrpclib.ServerProxy(_API)
    addr = Address.objects.filter(address=address)
    bcast = False
    if len(addr) != 0:
        a = addr[0]
    elif address == "":
        bcast = True
    else:
        a = Address.objects.create(address=address, label='default')
        a.save()

    if request.method == 'POST':
        form = SendForm(request.POST)
        if form.is_valid():
            sender = form.cleaned_data['sender'].address
            message = form.cleaned_data['message'].encode('base64')
            subject = form.cleaned_data['subject'].encode('base64')
            if bcast:
                ackdata = api.sendBroadcast(sender, subject, message)
            else:
                ackdata = api.sendMessage(a.address, sender, subject, message)
            return HttpResponseRedirect('/outbox')

    fr = Identity.objects.filter(address=faddr)
    if len(fr) != 0: 
        form = SendForm(initial={'sender':fr[0]})
    else:
        form = SendForm()

    template = loader.get_template('bitmsgapi/send.html')
    if bcast:
        context = {'form': form}
    else:
        context = {'addr' : a, 'form': form}

    return render(request, 'bitmsgapi/send.html', context)

def new_address(request):
    api = xmlrpclib.ServerProxy(_API)
    if request.method == 'POST':
        form = NewAddress(request.POST)
        if form.is_valid():
            l = form.cleaned_data['label'].encode('base64')
            genaddr = api.createRandomAddress(l)
            return HttpResponseRedirect('/identities')
    form = NewAddress()

    template = loader.get_template('bitmsgapi/new_address.html')
    context = {'form': form}
    return render(request, 'bitmsgapi/new_address.html', context)

def subscribe(request):
    api = xmlrpclib.ServerProxy(_API)
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            l = form.cleaned_data['label'].encode('base64')
            a = form.cleaned_data['address']
            api.addSubscription(a, l)
            return HttpResponseRedirect('/addressbook')
    form = SubscribeForm()

    template = loader.get_template('bitmsgapi/subscribe.html')
    context = {'form':form}

    return render(request, 'bitmsgapi/subscribe.html', context)   
 

def join_chan(request):
    api = xmlrpclib.ServerProxy(_API)
    if request.method == 'POST':
        form = JoinChan(request.POST)
        if form.is_valid():
            p = form.cleaned_data['password'].encode('base64')
            a = form.cleaned_data['address']
            api.joinChan(p, a)
            return HttpResponseRedirect('/identities')
    form = JoinChan()

    template = loader.get_template('bitmsgapi/join_chan.html')
    context = {'form':form}
    return render(request, 'bitmsgapi/join_chan.html', context)

