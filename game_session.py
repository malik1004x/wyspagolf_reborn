from xml_functions import makeXMLLine


class GameSession:
    turn_time = "100000"
    number_of_levels = 12

    def __init__(self, starter, opponent):
        self.current_level = 1
        self.starter = starter
        self.opponent = opponent
        starter.session = self
        opponent.session = self
        self.current_player = starter

    def sendLoadLevel(self, level_number, first_player):
        line = makeXMLLine(
            "startLevel",
            {
                "nr": str(level_number),
                "pn": first_player,
                "t": self.turn_time
            }
        ).encode("utf-8")
        self.sendToBoth(line)

    def nextLevel(self, first_player):
        self.starter.pocketed = False
        self.opponent.pocketed = False
        if self.current_level == self.number_of_levels:
            self.endGame()
        else:
            self.current_level += 1
            self.sendLoadLevel(self.current_level, first_player)

    def loadGame(self):
        self.opponent.sendStartGame(self.starter.username)
        self.starter.sendStatusUpdate(started_playing=True)
        self.opponent.sendStatusUpdate(started_playing=True)
        # self.sendLoadLevel(self.current_level, self.starter.username)

    def checkClientInitiated(self):
        if self.starter.clientInitiated and self.opponent.clientInitiated:
            self.sendLoadLevel(self.current_level, self.current_player.username)

    def getOtherClient(self, client):
        if client is self.starter:
            return self.opponent
        else:
            return self.starter

    def sendToOtherPlayer(self, client, line):
        recipient = self.getOtherClient(client)
        recipient.sendLine(line)

    def sendTurnToOtherPlayer(self, client, x, y, p, r, fp):
        self.sendToOtherPlayer(
            client,
            makeXMLLine(
                "turn",
                {"x": x, "y": y, "p": p, "r": r, "fp": fp}
            ).encode("utf-8")
        )

    def messageOtherPlayer(self, client, msg):
        self.sendToOtherPlayer(
            client,
            makeXMLLine(
                "msgPlayer",
                {"name": client.username,
                 "msg": msg}
            ).encode("utf-8")
        )

    def callSurrender(self, client):
        winner = self.getOtherClient(client)
        line = makeXMLLine(
            "surrender",
            {
                "winner": winner.username
            }
        ).encode("utf-8")
        self.sendToBoth(line)

    def handleReady(self):
        if self.starter.ready and self.opponent.ready:
            self.starter.ready = False
            self.opponent.ready = False
            if self.starter.pocketed and self.opponent.pocketed:
                self.nextLevel(self.current_player.username)
            else:
                self.startNextTurn()

    def startNextTurn(self):
        # now it's the other player's turn.
        previous_player = self.current_player
        other_player = self.getOtherClient(previous_player)
        if not other_player.pocketed:
            self.current_player = other_player
        line = makeXMLLine(
                "nextTurn",
                {
                    "n": self.current_player.username,
                    "t": "100000",
                    "x1": str(self.current_player.ballPosAfterTurn[0]),
                    "y1": str(self.current_player.ballPosAfterTurn[1]),
                    "x2": str(previous_player.ballPosAfterTurn[0]),
                    "y2": str(previous_player.ballPosAfterTurn[1]),
                }
            ).encode("utf-8")

        self.sendToBoth(line)

    def sendToBoth(self, line):
        self.opponent.sendLine(line)
        self.starter.sendLine(line)

    def getWinnerName(self):
        if self.starter.hitNumber > self.opponent.hitNumber:
            return self.opponent.username
        elif self.starter.hitNumber < self.opponent.hitNumber:
            return self.starter.username
        else:
            return ""  # an empty string is interpreted by the client as a draw.

    def endGame(self):
        line = makeXMLLine(
            "endGame",
            {
                "winner": self.getWinnerName()
            }
        ).encode("utf-8")
        self.sendToBoth(line)

    def endSession(self):
        for client in (self.starter, self.opponent):
            client.hitNumber = 0
            client.pocketed = False
            client.clientInitiated = False
            client.ready = False
            client.session = None
            client.sendStatusUpdate(started_playing=False)
        self.starter.factory.game_sessions.remove(self)
