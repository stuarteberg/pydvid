import os
import getpass
import inspect
import functools
import threading
from collections import namedtuple

import requests
from libdvid import DVIDNodeService

DEFAULT_DVID_SESSIONS = {}
DEFAULT_DVID_NODE_SERVICES = {}
DEFAULT_APPNAME = "neuclease"

# FIXME: This should be eliminated or at least renamed
DvidInstanceInfo = namedtuple("DvidInstanceInfo", "server uuid instance")

def default_dvid_session(appname=None):
    """
    Return a default requests.Session() object that automatically appends the
    'u' and 'app' query string parameters to every request.
    """
    if appname is None:
        appname = DEFAULT_APPNAME
    # Technically, request sessions are not threadsafe,
    # so we keep one for each thread.
    thread_id = threading.current_thread().ident
    pid = os.getpid()
    try:
        s = DEFAULT_DVID_SESSIONS[(appname, thread_id, pid)]
    except KeyError:
        s = requests.Session()
        s.params = { 'u': getpass.getuser(),
                     'app': appname }
        DEFAULT_DVID_SESSIONS[(appname, thread_id, pid)] = s

    return s


def default_node_service(server, uuid, appname=None):
    if appname is None:
        appname = DEFAULT_APPNAME

    # One per thread/process
    thread_id = threading.current_thread().ident
    pid = os.getpid()

    try:
        ns = DEFAULT_DVID_NODE_SERVICES[(appname, thread_id, pid, server, uuid)]
    except KeyError:
        ns = DVIDNodeService(server, str(uuid), getpass.getuser(), appname)

    return ns


def dvid_api_wrapper(f):
    """
    Decorator for functions whose first arg is a dvid server address,
    and accepts 'session' as a keyword-only argument.
    
    This decorator does the following:
    - If the server address begins with 'http://', that prefix is stripped from it.
    - If 'session' was not provided by the caller, a default one is provided.
    - If an HTTPError is raised, the response body (if any) is also included in the exception text.
      (DVID error responses often include useful information in the response body,
      but requests doesn't normally include the error response body in the exception string.
      This fixes that.)
    """
    argspec = inspect.getfullargspec(f)
    assert 'session' in argspec.kwonlyargs, \
        f"Cannot wrap {f.__name__}: DVID API wrappers must accept 'session' as a keyword-only argument."
    
    @functools.wraps(f)
    def wrapper(server, *args, session=None, **kwargs):
        assert isinstance(server, str)
        if server.startswith('http://'):
            server = server[len('http://'):]

        if session is None:
            session = default_dvid_session()

        try:
            return f(server, *args, **kwargs, session=session)
        except requests.HTTPError as ex:
            # If the error response had content (and it's not super-long),
            # show that in the traceback, too.  DVID error messages are often helpful.
            if ( not hasattr(ex, 'response_content_appended')
                 and ex.response is not None
                 and ex.response.content
                 and len(ex.response.content) <= 200 ):
                
                msg = str(ex.args[0]) + "\n" + ex.response.content.decode('utf-8')
                new_ex = requests.HTTPError(msg, *args[1:])
                new_ex.response_content_appended = True
                raise new_ex from ex
            else:
                raise
    return wrapper


@dvid_api_wrapper
def fetch_generic_json(url, json=None, *, session=None):
    r = session.get('http://' + url, json=json)
    r.raise_for_status()
    return r.json()

