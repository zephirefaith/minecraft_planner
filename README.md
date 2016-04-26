#Minecraft Agent

A perception and action interface and HTN planner for solving 'puzzle rooms' in the Minecraft world. Uses Spockbot, a high-level Python client for the Minecraft server, and PyHop, a Python-based HTN planner created by Dana Nau and based on SHOP2. The minecraft-agent project was originally developed as part of Google Summer of Code 2015. That code is now part of a separate project, currently developed by OpenCog at [opencog-to-minecraft](https://github.com/opencog/opencog-to-minecraft).

##Prerequisites

####Ubuntu http://www.ubuntu.com

Recommended: Ubuntu Trusty (14.04).

####Minecraft server https://minecraft.net/download

Installation instructions for the Minecraft server are [here](http://minecraft.gamepedia.com/Tutorials/Setting_up_a_server)

You can also choose other Minecraft server managers. Code has not been tested with the integrated server used in single player.

####Spock
version 0.1.3

A python API to connect with Minecraft server.

The original repository, under heavy development, can be found [here](https://github.com/SpockBotMC/SpockBot)

A fixed state used for my projects is on my public GitHub [here](https://github.com/LucidBlue/SpockBot)

##Contents

`/utils` contains utility files for movement, perception, and sensation plugins. It also has constants that are used throughout the code base.
`/worlds` contains Minecraft test worlds. Note worlds were simply edited to remove chunk data in a certain radius around the spawn 'island'. Terrain still exists beyond this radius.

##Steps to run

1. add the following to your PYTHONPATH:

    `/path_to_minecraft-bot/`

2. Start the Minecraft Server. This step will differ depending on how you chose to set it up.

3. Follow instructions in [minecraft_bot](https://github.gatech.edu/bsheneman3/minecraft-bot/blob/master/minecraft_bot) to use Spock. You should see the bot appear in your Minecraft world. If you don't see it right away, a 'spawn' message should still appear in the chat dialogue, along with its coordinates.

4. You should see the bot move around (test_actions.py) or start printing out lists of blocks that it can see from a fixed position (test_visibility.py).

##TODO

* Finish documentation.

* Add more percepts: Entities, chat messages, etc.

* Greater perceptual range: The bot's FOV is constrained to about 10 units due to the (in)efficiency of the ray-tracing camera (see visibility.py).

* Use the idmap in minecraft_bot/src/embodiment-testing/ to replace block ids in the perception manager.

* write a script to start everything, or package using ROS. Probably an easy way to do this...
