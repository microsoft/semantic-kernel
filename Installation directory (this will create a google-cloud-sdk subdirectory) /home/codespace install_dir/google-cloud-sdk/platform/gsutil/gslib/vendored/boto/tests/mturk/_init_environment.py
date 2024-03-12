import os
import functools

live_connection = False
mturk_host = 'mechanicalturk.sandbox.amazonaws.com'
external_url = 'http://www.example.com/'


SetHostMTurkConnection = None

def config_environment():
    global SetHostMTurkConnection
    try:
            local = os.path.join(os.path.dirname(__file__), 'local.py')
            execfile(local)
    except:
            pass

    if live_connection:
            #TODO: you must set the auth credentials to something valid
            from boto.mturk.connection import MTurkConnection
    else:
            # Here the credentials must be set, but it doesn't matter what
            #  they're set to.
            os.environ.setdefault('AWS_ACCESS_KEY_ID', 'foo')
            os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'bar')
            from mocks import MTurkConnection
    SetHostMTurkConnection = functools.partial(MTurkConnection, host=mturk_host)
