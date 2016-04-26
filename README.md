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

    `/path_to_minecraft-agent/`

2. Start the Minecraft Server. This step will differ depending on how you chose to set it up.

3. Run `test_agent.py`. You should see the bot appear in your Minecraft world. If you don't see it right away, a 'spawn' message should still appear in the chat dialogue, along with its coordinates.

4. If the bot is not inside the given room, teleport it by typing the command into the chat dialogue box: `/tp Bot x, y, z`.

5. Place a block of gold in the world. The bot will invoke its planner, and then navigate to the gold.

##TODO

* Finish documentation.

* Add more percepts: `inventory_contents` and `held_object`.
