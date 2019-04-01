import os
import signal
import subprocess
import time

from protoactor.remote.remote import Remote, Serialization
from tests.remote.messages.protos_pb2 import DESCRIPTOR


class RemoteManager():
    def __init__(self):
        Serialization().register_file_descriptor(DESCRIPTOR)
        self.__nodes = {}
        self.__default_node_address = '127.0.0.1:12000'

        self.provision_node('127.0.0.1', 12000)
        Remote().start("127.0.0.1", 12001)

    @property
    def default_node_address(self):
        return self.__default_node_address

    @property
    def nodes(self):
        return self.__nodes

    def provision_node(self, host='127.0.0.1', port=12000):
        process = subprocess.Popen("python ./node/node.py --host %s --port %s" % (host, port),
                                   stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        address = '%s:%s' % (host, port)
        self.__nodes[address] = process
        time.sleep(3)
        return address, process

    def dispose(self):
        for process in self.__nodes.values():
            process.kill()
            process.wait()
        Remote().shutdown(False)