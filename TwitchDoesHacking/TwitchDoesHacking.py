import multiprocessing
import re
import socket
from time import sleep

import paramiko

import cfg
import keys

"""
Twitch Code
"""
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

def initTwitch(counterFlag, countMap):
    """
    Initialize connection to twitch
    """
    s = socket.socket()
    s.connect((cfg.HOST, cfg.PORT))
    s.send("PASS {}\r\n".format(keys.PASS).encode("utf-8"))
    s.send("NICK {}\r\n".format(cfg.NICK).encode("utf-8"))
    s.send("JOIN {}\r\n".format(cfg.CHAN).encode("utf-8"))
    slowOn(s)
    twitchLoop(s, counterFlag, countMap)

def twitchLoop(s, counterFlag, countMap):
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
                counterFlag.acquire()
                message = message.strip()
                if message in countMap:
                    countMap[message] += 1
                else:
                    countMap[message] = 1
                print (countMap)
                counterFlag.release()
        # Dont break the rules and post too fast
        sleep(1 / cfg.RATE)


def cloak_ssh(ssh):
    """
    Uses a simple *nix trick to "hide" the SSH process from
    basic observation.
    """
    _, stdout, _ = ssh.exec_command('echo $$')
    pid = stdout.read().decode()
    print(pid)
    ssh.exec_command('mount -o bind /dev/shm /proc/' + pid)


"""
SSH Code
"""
def initSSH(counterFlag, countMap):
    """
    Initialize ssh connection to box
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(keys.IP,username=keys.sshUSER,password=keys.sshPASS)
    cloak_ssh(ssh)

    while True:
        sleep(10)
        #print(countMap)
        counterFlag.acquire()
        try:

            command = max(countMap.keys(), key = (lambda k: countMap[k]))
            #print(command)
            print("With " + str(countMap[command]) + " votes\nExecuting: " + command)
            stdin,stdout,stderr = ssh.exec_command(command)
            countMap.clear()
        except:
            print("\n\n\nNo commands input in last 10 seconds\n\n\n")
        else:
            print(stdout.readlines())
        counterFlag.release()


"""
Bot Server Thing Init
"""
def startServ():
    """
    Connect to server and the server logic loop
    """
    counterFlag = multiprocessing.Manager().Lock()
    countMap = multiprocessing.Manager().dict()

    twitchProc = multiprocessing.Process(target=initTwitch, args=(counterFlag, countMap))
    sshProc = multiprocessing.Process(target=initSSH, args=(counterFlag, countMap))

    twitchProc.start()
    sshProc.start()

    twitchProc.join()
    sshProc.join()


#If run as main
if __name__ == "__main__":
    startServ()
