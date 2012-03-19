#!/usr/bin/env python

# pylint: disable-msg=W0402
from string import digits, letters, punctuation
from random import choice


def create_secret_key():
    """
    Creates a new SECRET_KEY for usage in local_settings.py.
    """
    alphabet = letters + digits + punctuation
    new_key = ''.join([choice(alphabet) for _ in range(50)])
    return new_key


if __name__ == "__main__":
    print '\nConvenience tool to create a secret key for local_settings.py.'
    print 'Copy the following line into your local_settings.py:\n'
    print "SECRET_KEY = {0!r}\n".format(create_secret_key())
    