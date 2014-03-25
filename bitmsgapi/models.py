from django.db import models

# Create your models here.

class Identity(models.Model):
    address = models.CharField(max_length=80,primary_key=True)
    label = models.CharField(max_length=100)
    def __unicode__(self):
        return str(self.address + " (" + self.label + ")")

class Address(models.Model):
    address = models.CharField(max_length=80,primary_key=True)
    label = models.CharField(max_length=100)
    def __unicode__(self):
        return str(self.address + " (" + self.label + ")")

class Message(models.Model):
    subject = models.CharField(max_length=200)
    msg_from = models.ForeignKey(Address)
    msg_to = models.ForeignKey(Identity)
    msg_unread = models.BooleanField(default=True)
    rcv_date = models.DateTimeField('date received')
    msg = models.TextField()

    class Meta:
        ordering = ('-rcv_date',)
        
    def __unicode__(self):
        return self.subject

class OutMessage(models.Model):
    subject = models.CharField(max_length=200)
    msg_from = models.ForeignKey(Identity)
    msg_to = models.ForeignKey(Address)
    msg_status = models.CharField(max_length=200)
    last_action_date = models.DateTimeField('last action date')
    msg = models.TextField()
    msg_id = models.CharField(max_length=100)

    class Meta:
        ordering = ('-last_action_date',)
        
    def __unicode__(self):
        return self.subject


