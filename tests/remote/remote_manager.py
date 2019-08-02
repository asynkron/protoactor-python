import subprocess
import time

from protoactor.remote.remote import Remote, Serialization
from tests.remote.messages.protos_pb2 import DESCRIPTOR


class RemoteManager():
    def __init__(self):
        Serialization().register_file_descriptor(DESCRIPTOR)
        self.__nodes = {}
        self.__default_node_address = 'localhost:12000'

        self.provision_node('localhost', 12000)
        Remote().start("localhost", 12001)

    @property
    def default_node_address(self):
        return self.__default_node_address

    @property
    def nodes(self):
        return self.__nodes

    def provision_node(self, host='localhost', port=12000):
        process = subprocess.Popen(['python', './node/node.py', '--host', str(host), '--port', str(port)],
                                   stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE)
        address = '%s:%s' % (host, port)
        self.__nodes[address] = process
        time.sleep(10)
        return address, process

    def dispose(self):
        for process in self.__nodes.values():
            process.kill()
            process.wait()
        Remote().shutdown(False)