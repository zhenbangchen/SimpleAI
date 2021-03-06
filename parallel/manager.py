from multiprocessing import Lock
from multiprocessing.managers import BaseManager, State
from functools import partial

default_ip = '127.0.0.1'
default_port = 1995
default_auth_key = b'0813'

class Weights(object):
    def __init__(self):
        self.value = list()
        self.update_id = -1
        self.lock = Lock()

    def get_id(self):
        return self.update_id

    def update(self, new_weights, update_id=None):
        with self.lock:
            self.value[:] = new_weights
            if update_id is None:
                self.update_id += 1
            else:
                self.update_id = update_id
        return self.get_id()

    def get(self):
        return self.value

class ParallelObject(object):
    def __init__(self, instance, manager, identity):
        self.object = None
        self.manager = manager
        self.identity = identity
        for attr in dir(instance):
            if attr.startswith('_') or not callable(getattr(instance, attr, None)):
                continue
            setattr(self, attr, partial(self._call_anything, attr))

    def check(self):
        if self.object is None:
            self.start()

    def start(self):
        if self.manager._state.value == State.INITIAL:
            self.manager.connect()
        self.object = getattr(self.manager, self.identity)()

    def set_instance(self, instance):
        self.object = instance

    def _call_anything(self, name, *args, **kwargs):
        self.check()
        return getattr(self.object, name)(*args, **kwargs)


class ServerManager(BaseManager): pass
class ClientManager(BaseManager): pass

def echoback(x):
    return x

def register_server(**kwargs):
    #  call before `new_server()`
    for key, value in kwargs.items():
        ServerManager.register(key, callable=partial(echoback, value))

def register_client(*args):
    #  call before `new_client()`
    for key in args:
        ClientManager.register(key)

def new_server(ip=default_ip, port=default_port, auth_key=default_auth_key):
    manager = ServerManager(('0.0.0.0', port), auth_key)
    return manager

def new_client(ip=default_ip, port=default_port, auth_key=default_auth_key):
    manager = ClientManager((ip, port), auth_key)
    return manager