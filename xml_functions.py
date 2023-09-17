import re


def parseXML(data):
    # parses the xml received from the game.
    # example:
    # <msgAll name="malik" msg="i like cats"/>
    # command is msgAll
    # params is dict(name="malik", msg="i like cats")
    command = data[1:].split(" ", 1)[0].replace("/>", "")
    params = dict(re.findall('(\w+)="(.+?)"', data))
    return command, params


def makeXMLLine(command, params=None, sharp_end=True):
    # this takes a string and dict and makes xml in the format the game expects
    string = "<"
    string += command  # string is now "<command"
    if params is not None:
        for param in params:  # example: {'foo': 'bar'} will add ' foo="bar"'
            string += f" {param}=\"{params[param]}\""

    if sharp_end:
        string += "/>"
    else:
        string += ">"
    return string


def makeXMLWithContent(command, params=None, value=None):
    string = makeXMLLine(command, params, sharp_end=False)
    if value is not None:
        string += value
    string += f"</{command}>"
    return string
