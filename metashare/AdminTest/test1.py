'''
Created on Feb 3, 2012

@author: Administrator
'''

import settings
from django.shortcuts import render_to_response
from django.forms import ModelForm
from django.forms.models import ModelFormMetaclass
from django.forms.formsets import formset_factory
from django.template import RequestContext

from models import PersonInfo

def test():
    p = PersonInfo()
    print p
    #p.full_clean()
    
    bases = (ModelForm, )
    Meta = type('Meta', (object,), {'model': PersonInfo})
    attrs = {'Meta': Meta}
    personForm = ModelFormMetaclass('PersonForm', bases, attrs)
    data = {'name': 'Nome', 'surname': 'Cognome', 'email': 'a@b.com'}
    data1 = {}
    pf = personForm(data=data1, prefix='abc')
    print pf
    #pf.clean()
    
    PersonFormset = formset_factory(personForm, extra=2)
    pfs = PersonFormset(prefix='mmmm')
    print
    print 'Formset'
    print pfs
    
def view(request):
    print "Request"
    test()
    context = {}
    return render_to_response('main.html', context,
                              context_instance=RequestContext(request))
