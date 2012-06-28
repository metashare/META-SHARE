'''
Created on Feb 3, 2012

@author: Administrator
'''

from django.db.models import Model
from django.db.models.fields import CharField, EmailField
from django.db.models.fields.related import ForeignKey
from django.contrib import admin

from metashare.AdminTest.admin import TestAdmin, TestInline
from metashare.AdminTest.admin2 import TestAdmin2

class OrganizationInfo(Model):
    name = CharField(blank=False, max_length=100)
    
    def __unicode__(self):
        return u'{0}'.format(self.name)

class PersonInfo(Model):
    name = CharField(blank=False, max_length=100)
    surname = CharField(blank=False, max_length=100)
    org = ForeignKey(OrganizationInfo)
    
    def __unicode__(self):
        return u'{0} {1}'.format(self.name, self.surname)

class CommunicationInfo(Model):
    email = EmailField(blank=False)
    tel = CharField(blank=True, max_length=30)
    person = ForeignKey(PersonInfo)

    def __unicode__(self):
        return u'Email: {0}'.format(self.email)

TEST_NESTED = True
TEST_VERSION = 2

if TEST_NESTED:
    class CommunicationInline(TestInline):
        model = CommunicationInfo
        
    class PersonAdmin(TestAdmin):
        inlines = [CommunicationInline, ]
    
    class PersonInline(TestInline):
        model = PersonInfo
        inlines = [CommunicationInline,]
        
    if TEST_VERSION == 1:
        class OrganizationAdmin(TestAdmin):
            inlines = [PersonInline, ]
    else:
        class OrganizationAdmin(TestAdmin2):
            inlines = [PersonInline, ]
else:
    class CommunicationInline(admin.StackedInline):
        model = CommunicationInfo
        
    class PersonAdmin(admin.ModelAdmin):
        inlines = [CommunicationInline, ]
    
    class PersonInline(admin.StackedInline):
        model = PersonInfo
        inlines = [CommunicationInline,]
        
    class OrganizationAdmin(admin.ModelAdmin):
        inlines = [PersonInline, ]
    
admin.site.register(PersonInfo, PersonAdmin)
admin.site.register(OrganizationInfo, OrganizationAdmin)
admin.site.register(CommunicationInfo)
