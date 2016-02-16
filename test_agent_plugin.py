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

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

__author__ = 'Cosmo Harrigan, Morgan Creekmore, Bradley Sheneman'

logger = logging.getLogger('spockbot')

# Required class decorator
@pl_announce('TestAgentPlugin')
class TestAgentPlugin(PluginBase):

    requires = ('Movement', 'Timers', 'World', 'ClientInfo', 'Inventory',
                'Interact', 'Chat')

    events = {
        'client_join_game':     'handle_client_join',
        'inventory_synced':     'handle_inventory',
        'PLAY<Chat Message':    'handle_chat',
    }


    def __init__(self, ploader, settings):
        super(ExamplePlugin, self).__init__(ploader, settings)

        # starting location of agent
        self.target_coords = Vector3(10., 2., 10.)

        frequency = 5  # in seconds
        self.timers.reg_event_timer(frequency, self.periodic_event_handler)


    def handle_client_join(self, name, data):
        """ Verifies agent has started correctly, then
            moves to starting location (i.e. the room)."""

        self.chat.chat('agent is moving to start location...')
        self.movement.move_to(*TARGET_COORDINATES)
        self.chat.chat('agent has arrived at start location.')


    def handle_inventory(self, name, data):
        # select an oak wood plank
        self.select_block(5)


    def handle_chat(self, name, data):
        """ Called when a chat message occurs in the game
            Allows using custom chat commands to control the bot"""

        logger.info('Chat message received: {0}'.format(data))
        ############################
        # control related code here
        ############################


    def select_block(self, block_id):
        # Search hotbar for block. if not found, return None
        desired_slot = None
        found_slot = self.inventory.find_slot(
            block_id,
            self.inventory.window.hotbar_slots)

        # if not found, search the rest of inventory
        if found_slot is None:
            found_slot = self.inventory.find_slot(
                block_id,
                self.inventory.window.inventory_slots)

        # if still not found, print to log
        if found_slot is None:
            logger.info('No block with ID: {0} found'.format(
            block_id))
        else:
            #self.inventory.drop_slot(drop_stack=True)
            self.inventory.click_slot(slot)
            self.inventory.click_slot(0)
            self.inventory.select_active_slot(0)


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
