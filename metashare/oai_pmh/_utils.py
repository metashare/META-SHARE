# coding=utf-8
# pylint:

"""
    Helpers.

    @author: jm (UFAL, Charles University in Prague)
    @www: http://ufal-point.mff.cuni.cz
    @version: 0.1
"""

import os
import json
import time


def params( d, param_list ):
    """
        Check parameters and return the values or raise
        AttributeError if missing.
    """
    for param in d:
        if not param in d:
            raise AttributeError("Missing [%s] parameter", param)
    if 1 == len(param_list):
        return d[param_list[0]]
    else:
        return [d[param] for param in param_list]


def prehtmlify( obj, add_pre=True ):
    """
        Make object nicely displayable in <pre>.
    """
    if not obj is None:
        str_ = u"%s" % json.dumps(obj, indent=2)
        return u"<pre style=\"margin:0;font-size:8pt\">%s</pre>" % str_ \
            if add_pre else str_
    return u"Invalid"


def smart_extend( dict_inst, *dict_arr ):
    """
        Recursively add items at every level to
        dict_inst rather than simply update.
    """
    for a in dict_arr:
        dict_inst.update(a)
    return dict_inst


def time_it( func, *args, **kwargs ):
    """
        Time a function.
        Alternative implement as a decorator.
    """
    t1 = time.time()
    ret = func(*args, **kwargs)
    t2 = time.time()
    return t2 - t1, ret


# noinspection PyBroadException
def safe_remove( file_str ):
    """ Do not raise if not successful. """
    try:
        os.remove(file_str)
    except:
        pass


def html_mark_error( s ):
    """ Simple mark error using html and css. """
    return u"<div style='color:red;font-size:120%%'>%s</div>" % s


def html_mark_warning( s ):
    """ Simple mark warning using html and css. """
    return u"<div style='color:orange;font-size:110%%'>%s</div>" % s
