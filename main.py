from twisted.internet import reactor, endpoints
from pub_factory import PubFactory


endpoints.serverFromString(reactor, "tcp:2468").listen(PubFactory())
reactor.run()
