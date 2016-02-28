1"""
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


# compass directions in yaw values
NORTH = 0
WEST = 90
SOUTH = 180
EAST = 270

EPSILON_DIST = 0.1
EPSILON_DIR  = 1.0

@pl_announce('SelfMovementSensor')
class SelfMovementSensorPlugin(PluginBase):

    requires = ('Movement', 'Timers', 'World', 'ClientInfo', 'Inventory',
                'Interact',
    )
    events = {
        'movement_position_reset':  'handle_position_reset'
        'movement_path_done':       'handle_path_done'
        #'client_join_game':         'handle_client_join',
        #'inventory_synced':         'handle_inventory',
        #'chat':                     'handle_chat',
    }


    def __init__(self, ploader, settings):
        super(SelfMovementSensorPlugin, self).__init__(ploader, settings)
        logger.info("Initializing SelfMovementSensor Plugin")

        # the agent's records of its own motion. updates every x seconds
        # will be an integer block position, with the agent at the center
        self.pos = None
        # NORTH, SOUTH, WEST, EAST
        self.dir = None
        # whether the agent is currently moving (forward) or turning
        # self.moving = False
        # self.turning = False

        frequency = 1  # in seconds
        self.timers.reg_event_timer(frequency, self.sensor_timer_tick)



    # not a normal event handler. simply triggered every x seconds
    def sensor_timer_tick(self):
        self.handle_update_sensors(self)

    def handle_update_sensors(self):
        client_pos = self.clientinfo.position
        self.facing = get_nearest_direction(client_pos.yaw)
        self.pos = Vector3(*get_nearest_position(client_pos.x,client_pos.y,client_pos.z))


    def get_nearest_direction(self, yaw):
        deg_from = [(abs(NORTH - yaw),'NORTH'),
                    (abs(SOUTH - yaw),'SOUTH'),
                    (abs(WEST - yaw), 'WEST'),
                    (abs(EAST - yaw), 'EAST'),]
        diff,facing = min(deg_from)
        logger.info("facing {} with a deviation of {}").format(facing, diff)
        return facing


    def get_nearest_position(x, y, z):
        pos = (math.floor(x),math.floor(y),math.floor(z))
        logger.info("at position {} with original {}").format(pos, (x,y,z))
        return pos


    def is_turning():
        diff = abs(self.absolute_dir - self.clientinfo.position.yaw)
        if diff > EPSILON_DIR:
            return True
        return False


    def is_moving():
        dist = math.sqrt(
            (self.absolute_pos.x - self.clientinfo.position.x)**2 +
            (self.absolute_pos.y - self.clientinfo.position.y)**2 +
            (self.absolute_pos.z - self.clientinfo.position.z)**2)
        if dist > EPSILON_DIST:
            return True
        return False

    """
    def periodic_event_handler(self):
        logger.info('My position: {0} pitch: {1} yaw: {2}'.format(
            self.clientinfo.position,
            self.clientinfo.position.pitch,
            self.clientinfo.position.yaw))

        # Place a block in front of the player
        self.interact.place_block(
            self.clientinfo.position + Vector3(-1, 0, -1))

        # Read a block under the player
        block_pos = self.clientinfo.position.floor()
        block_id, meta = self.world.get_block(*block_pos)
        block_at = blocks.get_block(block_id, meta)
        self.chat.chat('Found block %s at %s' % (
            block_at.display_name, block_pos))
    """
