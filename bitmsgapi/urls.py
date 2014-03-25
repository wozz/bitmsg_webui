from django.conf.urls import patterns, url

from bitmsgapi import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^inbox$', views.inbox, name='inbox'),
    url(r'^outbox$', views.outbox, name='outbox'),
    url(r'^addressbook$', views.addressbook, name='addressbook'),
    url(r'^identities$', views.identities, name='identities'),
    url(r'^new_address$', views.new_address, name='new_address'),
    url(r'^subscribe$', views.subscribe, name='subscribe'),
    url(r'^join_chan$', views.join_chan, name='join_chan'),
    url(r'^msg/(?P<msg_id>\d+)$', views.msg, name='msg'),
    url(r'^rawmsg/(?P<msg_id>\d+)$', views.rawmsg, name='rawmsg'),
    url(r'^omsg/(?P<msg_id>\d+)$', views.omsg, name='omsg'),
    url(r'^send/(?P<address>.+)/(?P<fm>\d+)$', views.send, name='send'),
    url(r'^send/(?P<address>.+)$', views.send, name='send'),
    url(r'^send$', views.send, name='send'),
    url(r'^del_addr/(?P<address>.+)$', views.del_addr, name='del_addr'),
)
