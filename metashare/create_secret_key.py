#!/usr/bin/env python

import string
from random import choice
alphabet = string.letters + string.digits + string.punctuation
while True:
  SECRET_KEY = ''.join([choice(alphabet) for i in range(50)])
  if not "'" in SECRET_KEY:
    break

print 'Convenience tool to create a secret key for local_settings.py.'
print 'Copy the following line into your local_settings.py:\n'
print "SECRET_KEY = '{0}'".format(SECRET_KEY)

