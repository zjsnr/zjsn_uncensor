import socket


def getIP():
    return socket.gethostbyname(socket.gethostname())
