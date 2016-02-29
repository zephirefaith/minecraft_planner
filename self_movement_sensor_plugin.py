"""
An example plugin for spockbot

Demonstrates the following functionality:
- Receiving chat messages
- Sending chat commands
- Using inventory
- Moving to location
- Triggering a periodic event using a timer
- Registering for an event upon startup
- Placing blocks
- Reading blocks
"""
import logging
import math

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from test_room_plugin import TestRoomPlugin


__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


# tick frequency for movement sensor
FREQUENCY = 1

# compass directions in yaw values
NORTH = 0
WEST = 90
SOUTH = 180
EAST = 270

# acceptable error to test whether agent has stopped moving
EPSILON_DIST = 1./10
EPSILON_DIR  = 90./10


# probably make this a subclass of some generic agent state
class AgentMovementState:
    def __init__(self, pos=None, facing=None, moving=None, turning=None):
        # x, y, z integer only
        self.pos = Vector3(*pos) if pos else None
        # cardinal directions only
        self.dir = facing
        # if the agent is moving or turning
        self.moving = moving
        self.turning = turning


@pl_announce('SelfMovementSensor')
class SelfMovementSensorPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World', 'Movement',
                'Inventory', 'Interact',
    )
    events = {
        'movement_position_reset':  'handle_position_reset',
        'movement_path_done':       'handle_path_done',
        'client_join_game':         'handle_client_join',
        #'inventory_synced':         'handle_inventory',
        #'chat':                     'handle_chat',
    }


    def __init__(self, ploader, settings):
        super(SelfMovementSensorPlugin, self).__init__(ploader, settings)

        # the agent's records of its own motion. updates every x seconds
        # will be an integer block position, with the agent at the center
        self.state = AgentMovementState()
        # actual position/direction used to compute moving/turning
        self.absolute_pos = None
        self.absolute_dir = None

        # timer to update the agent's knowledge of its own movement
        frequency = FREQUENCY
        self.timers.reg_event_timer(frequency, self.sensor_timer_tick)


    #########################################################################
    # Timers and event handlers
    #########################################################################

    # not a normal event handler. simply triggered every x seconds
    def sensor_timer_tick(self):
        self.handle_update_sensors()

        # TODO: This has to be called with some data. e.g. formatted state
        self.event.emit('agent_movement_state')


    def handle_client_join(self, name, data):
        logger.info("Initializing agent's internal movement state")
        self.handle_update_sensors()


    def handle_update_sensors(self):
        pos = self.clientinfo.position
        self.state.facing = self.get_nearest_direction(pos.yaw)
        x,y,z = self.get_nearest_position(pos.x, pos.y, pos.z)
        self.state.pos = Vector3(x,y,z)

        self.state.turning = self.is_turning()
        self.state.moving = self.is_moving()

        self.log_agent_state(self.state)


    def handle_position_reset(self, name, data):
        pass


    def handle_path_done(self, name, data):
        pass


    #########################################################################
    # Utility functions for updating personal state
    #########################################################################
    def get_nearest_direction(self, yaw):
        deg_from = [(abs(NORTH - yaw),'NORTH'),
                    (abs(SOUTH - yaw),'SOUTH'),
                    (abs(WEST - yaw), 'WEST'),
                    (abs(EAST - yaw), 'EAST'),]
        diff,facing = min(deg_from)
        logger.debug("facing {} with a deviation of {}".format(facing, diff))
        return facing


    def get_nearest_position(self, x, y, z):
        pos = (math.floor(x),math.floor(y),math.floor(z))
        logger.debug("at position {} with original {}".format(pos, (x,y,z)))
        return pos


    def is_turning(self):
        if self.absolute_dir is None:
            return False

        diff = abs(self.absolute_dir - self.clientinfo.position.yaw)
        if diff > EPSILON_DIR:
            return True
        return False


    def is_moving(self):
        if self.absolute_pos is None:
            return False

        dist = math.sqrt(
            (self.absolute_pos.x - self.clientinfo.position.x)**2 +
            (self.absolute_pos.y - self.clientinfo.position.y)**2 +
            (self.absolute_pos.z - self.clientinfo.position.z)**2)
        if dist > EPSILON_DIST:
            return True
        return False


    def log_agent_state(self, agent_state):
        logger.info(
            "current state:\n<x:{}, y:{}, z:{}, facing:{}, moving:{}, turning:{}>\n".format(
                agent_state.pos.x,
                agent_state.pos.y,
                agent_state.pos.z,
                agent_state.facing,
                agent_state.moving,
                agent_state.turning,)
        )
