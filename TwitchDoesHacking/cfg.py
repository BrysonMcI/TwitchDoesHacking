"""
Config options for the bot
"""

import re

HOST = "irc.chat.twitch.tv"                   # the Twitch IRC server
PORT =  6667                                  # 443 = SSL, 6667 = normal
NICK = "twitchdoeshacking"                    # your Twitch username, lowercase
CHAN = "#twitchdoeshacking"                   # the channel you want to join

SLOW = "10"                                   # Slow mode timer

CHAT_MSG=re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

RATE = (90/30) # messages per second

PATT = [
    r"rm -rf",
    r"reboot"
]