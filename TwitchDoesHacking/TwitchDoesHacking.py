import re
import socket
from multiprocessing import Process, Manager
from time import sleep

import paramiko

import cfg
import keys


class Twitch(Process):
    """
    Twitch code
    """

    def __init__(self, counterFlag, countMap):
        """
        Initialize connection to twitch
        """
        self.s = socket.socket()
        self.s.connect((cfg.HOST, cfg.PORT))
        self.s.send("PASS {}\r\n".format(keys.PASS).encode("utf-8"))
        self.s.send("NICK {}\r\n".format(cfg.NICK).encode("utf-8"))
        self.s.send("JOIN {}\r\n".format(cfg.CHAN).encode("utf-8"))
        self.slowOn(self.s)
        self.counterFlag = counterFlag
        self.countMap = countMap
        super().__init__()

    def chat(self, msg):
        """
        Send a chat message to the server.
        Keyword arguments:
        sock -- the socket over which to send the message
        msg  -- the message to be sent
        """
        self.s.send("PRIVMSG {} :{}\r\n".format(cfg.CHAN, msg).encode("utf-8"))

    def ban(self, user):
        """
        Ban a user from the current channel.
        Keyword arguments:
        sock -- the socket over which to send the ban command
        user -- the user to be banned
        """
        self.chat("/ban {}".format(user))

    def timeout(self, user, secs=600):
        """
        Time out a user for a set period of time.
        Keyword arguments:
        sock -- the socket over which to send the timeout command
        user -- the user to be timed out
        secs -- the length of the timeout in seconds (default 600)
        """
        self.chat("/timeout {} {}".format(user, secs))

    def slowOn(self, time=int(cfg.SLOW)):
        """
        Enable slow mode
        """
        self.chat("/slow {}".format(time))

    def quit(self):
        self.chat("/quit got hacked :-/")

    def run(self):
        """
        Handles reading and banning on the server
        """
        while True:
            response = self.s.recv(1024).decode("utf-8")
            if response == "PING :tmi.twitch.tv\r\n":
                """
                Make sure twitch doesnt close us out
                """
                self.s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            elif response:
                username = re.search(r"\w+", response).group(0)  # return the entire match
                message = cfg.CHAT_MSG.sub("", response)
                print(username + ": " + message)
                for pattern in cfg.PATT:  # Ban if they type something in pat
                    if re.match(pattern, message):
                        self.timeout(username)
                        break
                if username != cfg.NICK and username != "" and username != "tmi":  # Check if we or server sent
                    self.counterFlag.acquire()
                    message = message.strip()
                    if message in self.countMap:
                        self.countMap[message] += 1
                    else:
                        self.countMap[message] = 1
                    print(self.countMap)
                    self.counterFlag.release()
            # Dont break the rules and post too fast
            sleep(1 / cfg.RATE)


"""
SSH Code
"""
def initSSH(counterFlag, countMap, twitch):
    """
    Initialize ssh connection to box
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(keys.IP, username=keys.sshUSER, password=keys.sshPASS)

    while True:
        sleep(10)
        # print(countMap)
        counterFlag.acquire()
        try:
            command = max(countMap.keys(), key=(lambda k: countMap[k]))
            print("With", str(countMap[command]), "votes\nExecuting:", command)
            stdin, stdout, stderr = ssh.exec_command(command)
            countMap.clear()
        except:
            print("\n\n\nNo commands input in last 10 seconds\n\n\n")
        else:
            out = stdout.readlines()
            print(out)
            twitch.chat(out)
        finally:
            counterFlag.release()


"""
Bot Server Thing Init
"""
def startServ():
    """
    Connect to server and the server logic loop
    """
    with Manager() as manager:
        counterFlag = manager.Lock()
        countMap = manager.dict()

        twitchProc = Twitch(counterFlag, countMap)
        sshProc = Process(target=initSSH, args=(counterFlag, countMap, twitchProc))

        twitchProc.start()
        sshProc.start()

        twitchProc.join()
        sshProc.join()


# If run as main
if __name__ == "__main__":
    startServ()
