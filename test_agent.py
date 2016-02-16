"""
Test agent. First version of the minecraft agent, which will function in a 2D
world (i.e. a slice of the 3D world) and solve a simple bridge problem.
Modified from example_plugin found in the original SpockBot repository
"""

import logging

# custom plugin. can be placed anywhere that is accessible
from test_agent_plugin import TestAgentPlugin

# spock utilities and plugins
from spockbot import Client
from spockbot.plugins import default_plugins

__author__ = 'Bradley Sheneman'

logger = logging.getLogger('spockbot')
logger.setLevel(logging.DEBUG)

# this will only work if the server is set to offline mode
# to use online mode, USERNAME and PASSWORD must be for a valid MC account
# server is simply the name of the server. port is below (25565 by default)
USERNAME = 'testagent'
PASSWORD = ''
SERVER = 'localhost'

settings = {
    'start': {
        'username': USERNAME,
        'password': PASSWORD,
    },
}

# Any functionality that you want must be implemented in a plugin.
# You can define new plugins that listen for events from the game.
plugins = default_plugins
plugins.append(('testagent', TestAgentPlugin))

# Instantiate and start the client
client = Client(plugins=plugins, settings=settings)
client.start(SERVER, 25565)
