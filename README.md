# chequemate-agents
Automations for chequemate.space

This repository hosts the smart tools that enhance user experience on chequemate.space (unpublished). Here is a brief description of these tools:

1. Match makers
These tools rely on player statistics—specifically elo rating, recent win streak, ECO profile, and prefered time settings—to match a player with another one depending on their present appetite for challenge. They rely on the chess.com and lichess.org APIs to retrieve this innformation. The aforementioned metrics are not provided by these APIs and are instead calculated within `chess.com_match_maker.py` and `lichess_match_maker.py`.

2. Chat moderator
This tool relies on Google's Perspective API to moderate chats between users. Comments that potentially violate community guidelines are identified and an agreeable alternative is suggested by using OpenAI API or XAI API to revise the intendedd text.

#### Terms
ECO: Encyclopedia of Chess Openings