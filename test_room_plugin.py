"""
An basic puzzle room. Creates the room, sets a start location and range

useful methods from Dimension (extended by World plugin):
    get_block() # get the block at a location
    get_block_entity_data() # get entity info at a location
    get_light() # get light level at location
    get_biome() # get biome at location
"""

import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

__author__ = 'Bradley Sheneman'

logger = logging.getLogger('spockbot')


# room coordinates (found in test_room_island)
MIN_X = -70
MIN_Y = 13
MIN_Z = -54

MAX_X = -62
MAX_Y = 15
MAX_Z = -38

START_COORDS = (-66,13,-39)


@pl_announce('TestRoomPlugin')
class TestRoomPlugin(PluginBase):

    requires = ('Timers', 'World', 'ClientInfo')

    events = {
        'world_block_update':   'handle_block_update',
    }

    # eventually __init__ will create the room
    # at a specified location
    def __init__(self, ploader, settings):
        super(TestRoomPlugin, self).__init__(ploader, settings)

        # starting location of agent
        self.dimensions = {
            'min_x': MIN_X,
            'min_y': MIN_Y,
            'min_z': MIN_Z,
            'max_x': MAX_X,
            'max_y': MAX_Y,
            'max_z': MAX_Z,
        }
        self.start_location = Vector3(*START_COORDS)

        #frequency = 5  # in seconds
        #self.timers.reg_event_timer(frequency, self.periodic_event_handler)


    def handle_block_update(self, name, data):
        pass


    def in_range(x, y, z):
        if (x < self.dimensions['min_x'] or
            x > self.dimensions['max_x'] or
            y < self.dimensions['min_y'] or
            y > self.dimensions['max_y'] or
            z < self.dimensions['min_z'] or
            z > self.dimensions['max_z']):
            return False
        return True


    # note is_obstacle and is_gap ONLY WORK WITH BASIC BLOCKS
    # e.g. any block that is not air is considered an obstacle/walkable floor

    # checks the block above the given floor location to see if it is passable
    def is_obstacle(x, y, z):
        block = self.world.get_block(x, y+1, z)
        if block.id != 0:
            return True
        return False


    # checks the given floor location to see if it is a gap
    def is_gap(x, y, z):
        block = self.world.get_block(x, y, z)
        if block.id == 0:
            return True
        return False


    def is_traversable(x, y, z):
        if self.is_obstacle(x, y, z) or self.is_gap(x, y, z):
            return False
        return True


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
