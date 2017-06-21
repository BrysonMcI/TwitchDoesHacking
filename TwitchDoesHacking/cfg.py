"""
Config options for the bot
"""

import re

HOST = "irc.twitch.tv"                        # the Twitch IRC server
PORT =  6697                                   # 443 = SSL, 6667 = normal
NICK = "TwitchDoesHacking"                    # your Twitch username, lowercase

CHAN = "#twitchdoeshacking"                             # the channel you want to join

CHAT_MSG=re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

RATE = (90/30) # messages per second

PATT = [
    r"rm -rf",
    r"reboot"
]
