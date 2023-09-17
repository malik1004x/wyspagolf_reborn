from twisted.internet import protocol
from twisted.logger import Logger
from client_connection import ClientConnection


class PubFactory(protocol.Factory):
    log = Logger()

    def __init__(self):
        self.clients = {}
        self.conn_ids = {}
        self.game_sessions = set()

    def getClientByUsername(self, name):
        conn_id = self.conn_ids[name]
        return self.clients[conn_id]

    def buildProtocol(self, addr):
        return ClientConnection(self)
