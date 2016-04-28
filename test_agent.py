"""
Test agent. First version of the minecraft agent, which will function in a 2D
world (i.e. a slice of the 3D world) and solve a simple bridge problem.
Modified from example_plugin found in the original SpockBot repository
"""

import logging
import os
import sys

# custom plugins. can be placed anywhere that is accessible
from test_room_plugin import TestRoomPlugin
from test_agent_plugin import TestAgentPlugin

from self_movement_sensor_plugin import SelfMovementSensorPlugin
from sensor_timers_plugin import SensorTimersPlugin
from visual_sensor_plugin import VisualSensorPlugin
from percept_monitor_plugin import PerceptMonitorPlugin

from atomic_operators_plugin import AtomicOperatorsPlugin
from test_atomic_operators import TestAtomicOperatorsPlugin
from test_planner_plugin import WallPlannerPlugin

# spock utilities and plugins
from spockbot import Client
from spockbot.plugins import default_plugins
#sys.path.insert(0, os.path.abspath('../SpockBot-Extra'))
#from plugins.echo_packet import EchoPacketPlugin

__author__ = 'Bradley Sheneman'

logger = logging.getLogger('spockbot')
logger.setLevel(logging.INFO)

# this will only work if the server is set to offline mode
# to use online mode, USERNAME and PASSWORD must be for a valid MC account
# server is simply the name of the server. port is below (25565 by default)
USERNAME = 'Bot'
#PASSWORD = ''
SERVER = 'localhost'

settings = {
    'start':
        {'username': USERNAME},
    'auth':
        {'authenticated': False}}

# Any functionality that you want must be implemented in a plugin.
# You can define new plugins that listen for events from the game.
plugins = default_plugins
plugins.append(('TestRoom', TestRoomPlugin))

plugins.append(('SensorTimers', SensorTimersPlugin))
plugins.append(('SelfMovementSensor', SelfMovementSensorPlugin))
plugins.append(('VisualSensor', VisualSensorPlugin))
plugins.append(('PerceptMonitor', PerceptMonitorPlugin))

plugins.append(('AtomicOperators', AtomicOperatorsPlugin))
#plugins.append(('TestAtomicOperators', TestAtomicOperatorsPlugin))

plugins.append(('WallPlanner', WallPlannerPlugin))

#plugins.append(('echo', EchoPacketPlugin))
#plugins.append(('TestAgent', TestAgentPlugin))

# Instantiate and start the client
client = Client(plugins=plugins, settings=settings)
client.start(SERVER, 25565)
