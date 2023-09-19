from twisted.protocols import basic
from xml_functions import makeXMLLine, makeXMLWithContent, parseXML
from game_session import GameSession


class ClientConnection(basic.LineReceiver):
    # one instance of this class represents one game client connection.
    def __init__(self, factory):
        self.factory = factory
        self.delimiter = b"\x00"
        self.authed = False
        self.username = ""
        self.clientInitiated = False
        self.session = None
        self.ready = False
        self.ballPosAfterTurn = (0, 0)
        self.pocketed = False
        self.hitNumber = 0

    def authme(self, username):
        if username in self.factory.conn_ids.keys():
            self.kickWithError(f"Inny gracz już używa nicka {username}.\nSpróbuj dołączyć z innym nickiem.")
        else:
            print("join")
            self.username = username
            self.factory.conn_ids[username] = id(self)
            self.authed = True
            self.sendUserList()
            self.broadcastNewPlayer()

    def connectionMade(self):
        self.factory.clients[id(self)] = self

    def connectionLost(self, reason):
        if self.authed:
            self.broadcastPlayerLeft()
            if self.session is not None:
                self.session.endSession()
        self.factory.clients.pop(id(self))

    def kickWithError(self, reason, keep_connection=False):
        self.sendLine(
            makeXMLWithContent(
                command="errorMsg",
                value=reason,
            ).encode("utf-8")
        )
        # after receiving <errorMsg>, the games lock up on an error screen with no way out.
        # i'm not sure why you'd want to keep the connection running,
        # but i implemented this just in case.
        if not keep_connection:
            self.transport.loseConnection()

    def displayWarning(self, reason):
        self.sendLine(
            makeXMLLine(
                command="warning",
                params={
                    "name": self.username,
                    "msg": reason
                }
            ).encode("utf-8")
        )

    def sendUserList(self):
        # print("sending user list")
        player_list = []
        for client in self.factory.clients.values():
            name = client.username
            if client.session is None:
                state = "0"  # available to play
            else:
                state = "3"  # currently in-game
            player_list.append(
                makeXMLLine("player", {"name": name, "state": state})
            )
        self.sendLine(
            makeXMLWithContent(
                command="userList",
                value="".join(player_list)
            ).encode("utf-8")
        )

    def broadcastNewPlayer(self):
        self.broadcastLine(
            makeXMLLine(
                "newPlayer",
                {
                    "name": self.username,
                    "skill": "1000",
                    "state": "0"
                }
            ).encode("utf-8")
        )

    def broadcastPlayerLeft(self):
        self.broadcastLine(
            makeXMLLine(
                "playerLeft",
                {
                    "name": self.username,
                }
            ).encode("utf-8")
        )

    def sendStatusUpdate(self, started_playing):
        if started_playing:
            new_status = "3"
        else:
            new_status = "0"
        self.broadcastLine(
            makeXMLLine(
                "playerUpdate",
                {
                    "name": self.username,
                    "skill": "1000",
                    "state": new_status
                }
            ).encode("utf-8")
        )

    def sendLineToUser(self, user, msg):
        client = self.factory.getClientByUsername(user)
        client.sendLine(msg.replace(b"\n", b"\x00"))

    def broadcastLine(self, msg, send_to_self=False):
        for c in self.factory.clients.values():
            if c is not self or send_to_self:  # for the sender, the game already shows the message clientside
                c.sendLine(msg.replace(b"\n", b"\x00"))

    # def messageOpponent(self, msg):
    #     self.current_opponent.sendLine(
    #         makeXMLLine(
    #             "msgPlayer",
    #             {
    #                 "name": self.username,
    #                 "msg": msg
    #             }
    #         ).encode("utf-8")
    #     )

    def challengePlayer(self, name):
        if name == self.username:
            # we can't allow starting a game against yourself.
            return
        self.sendLineToUser(
            name,
            makeXMLLine(
                "request",
                {
                    "name": self.username
                }
            ).encode("utf-8")
        )

    def cancelChallengePlayer(self, name):
        if name == self.username:
            return
        self.sendLineToUser(
            name,
            makeXMLLine(
                "remRequest",
                {
                    "name": self.username
                }
            ).encode("utf-8")
        )

    def challengeAll(self):
        for name in self.factory.conn_ids.keys():
            self.challengePlayer(name)

    def cancelChallengeAll(self):
        for name in self.factory.conn_ids.keys():
            self.cancelChallengePlayer(name)

    def setupGameSession(self, name_of_opponent):
        session = GameSession(
            starter=self,
            opponent=self.factory.getClientByUsername(name_of_opponent)
        )
        self.factory.game_sessions.add(session)
        session.loadGame()

    def sendStartGame(self, name_of_opponent):
        self.sendLine(
            makeXMLLine(
                "startGame",
                {
                    "name": name_of_opponent
                }
            ).encode("utf-8")
        )

    # def sendLine(self, line):
    #     print(f"{self.username} {line}")
    #     super().sendLine(line)

    def lineReceived(self, line):
        # for some bizarre reason, lines sent by the game sometimes end with a \n.
        # we remove it here rather than fixing the game code
        # because i wanted the server to work on an original unmodded .swf.
        line_str = line.decode("utf-8").replace("\n", "")
        command, params = parseXML(line_str)
        match command:
            case "auth":
                # TODO: lock the other commands before client sends auth.
                #  that won't affect the games but will repel telnetters.
                self.authme(params["name"])
            case "beat":
                # the games send a <beat/> every 15 seconds.
                # i'm not sure what was the original intention behind this. for now, we just log it.
                self.factory.log.info(f"{self.username} beating.")
            case "challenge":
                self.challengePlayer(params["name"])
            case "challengeAll":
                self.challengeAll()
            case "remChallenge":
                self.cancelChallengePlayer(params["name"])
            case "remChallengeAll":
                self.cancelChallengeAll()
            case "surrender":
                self.session.callSurrender(self)
            case "startGame":
                self.setupGameSession(params["name"])
            case "clientInitiated":
                self.clientInitiated = True
                self.session.checkClientInitiated()
            case "msgAll":
                # just send what the client sent to all other clients.
                self.broadcastLine(line)
            case "turn":
                self.hitNumber += 1
                self.session.sendTurnToOtherPlayer(
                    self,
                    params["x"], params["y"], params["p"], params["r"], params["fp"]
                )
            case "ready":
                self.ready = True
                self.ballPosAfterTurn = (params["x"], params["y"])
                self.session.handleReady()
            case "msgPlayer":
                self.session.messageOtherPlayer(self, params["msg"])
            case "pocketed":
                self.pocketed = True
            case "playAgain":
                self.session.sendToOtherPlayer(self, makeXMLLine("playAgain").encode("utf-8"))
            case "toRoom":
                if self.session is not None:  # will be None if the other client already ended the session.
                    self.session.endSession()
            case _:
                self.sendLine("not implemented :(".encode("utf-8"))
                self.factory.log.warn("client sent unimplemented")
                print(line_str)
