"""
An basic puzzle room. Creates the room, sets a start location and range
"""
import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

__author__ = 'Bradley Sheneman'

logger = logging.getLogger('spockbot')


# create a room that is floating, to avoid other blocks
MIN_X = 0
MIN_Y = 100
MIN_Z = 0

MAX_X = 9
MAX_Y = 105
MAX_Z = 9

# Required class decorator
@pl_announce('TestRoomPlugin')
class TestRoomPlugin(PluginBase):

    requires = ('Timers', 'World', 'ClientInfo')

    events = {
        #'client_join_game':     'handle_client_join',
    }

    def __init__(self, ploader, settings):
        super(TestRoomPlugin, self).__init__(ploader, settings)

        # starting location of agent
        start_x = (MAX_X - MIN_X)//2 + 1
        start_y = MIN_Y + 1
        start_z = MIN_Z + 1
        self.start_location = Vector3(start_x, start_y, start_z)

        #frequency = 5  # in seconds
        #self.timers.reg_event_timer(frequency, self.periodic_event_handler)


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
