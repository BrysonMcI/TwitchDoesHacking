import cfg
import keys
import paramiko
import socket
import re
from time import sleep
from collections import Counter

def chat(sock, msg):
    """
    Send a chat message to the server.
    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    sock.send(("PRIVMSG {} :{}\r\n").format(cfg.CHAN, msg).encode("utf-8"))

def ban(sock, user):
    """
    Ban a user from the current channel.
    Keyword arguments:
    sock -- the socket over which to send the ban command
    user -- the user to be banned
    """
    chat(sock, "/ban {}".format(user))

def timeout(sock, user, secs=600):
    """
    Time out a user for a set period of time.
    Keyword arguments:
    sock -- the socket over which to send the timeout command
    user -- the user to be timed out
    secs -- the length of the timeout in seconds (default 600)
    """
    chat(sock, "/timeout {} {}".format(user, secs))

def slowOn(sock, time=int(cfg.SLOW)):
    """
    Enable slow mode
    """
    chat(sock, "/slow {}".format(time))

def initTwitch():
    """
    Initialize connection to twitch
    """
    s = socket.socket()
    s.connect((cfg.HOST, cfg.PORT))
    s.send("PASS {}\r\n".format(keys.PASS).encode("utf-8"))
    s.send("NICK {}\r\n".format(cfg.NICK).encode("utf-8"))
    s.send("JOIN {}\r\n".format(cfg.CHAN).encode("utf-8"))
    slowOn(s)
    return s

def initSSH():
    """
    Initialize ssh connection to box
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(keys.IP,username=keys.sshUSER,password=keys.sshPASS)

def twitchLoop(s, countMap):
    """
    Handles reading and banning on the server
    """
    while True:
        response = s.recv(1024).decode("utf-8")
        if response == "PING :tmi.twitch.tv\r\n":
            """
            Make sure twitch doesnt close us out
            """
            s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        elif(response is not None):
            username = re.search(r"\w+", response).group(0) # return the entire match
            message = cfg.CHAT_MSG.sub("", response)
            print(username + ": " + message)
            for pattern in cfg.PATT: #Ban if they type something in pat
                if re.match(pattern, message):
                    timeout(s, username)
                    break
            if username != cfg.NICK and username != "" and username != "tmi": #Check if we or server sent
                countMap.update([message.strip() + '\n'])
        # Dont break the rules and post too fast
        sleep(1 / cfg.RATE) 

def startServ():
    """
    Connect to server and the server logic loop
    """
    countMap = Counter()
    s = initTwitch()
    twitchLoop(s, countMap)
    
#If run as main
if __name__ == "__main__":
    startServ()
