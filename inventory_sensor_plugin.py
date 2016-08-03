import logging

#from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
#from spockbot.vector import Vector3

from utils.constants import *
#import utils.movement_utils as mvu

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

@pl_announce('InventorySensor')
class InventorySensorPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'Inventory')

    events = {
        #'client_join_game':         'handle_client_join',
        'sensor_tick_inventory':    'handle_inventory_tick',
    }

    def __init__(self, ploader, settings):
        super(InventorySensorPlugin, self).__init__(ploader, settings)
        self.inventory = {
            'wood' : False,
            'iron' : False,
            'steel': False,
        }
    #########################################################################
    # Timers and event handlers
    #########################################################################

    def handle_inventory_tick(self, name, data):
        self.update_sensors()
        data = { }
        self.event.emit('agent_inventory_percept', data)

    def handle_client_join(self, name, data):
        inv = self.inventory
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        self.state.pos = Vector3(x, y, z)
        facing = mvu.get_nearest_direction(pos.yaw)
        self.state.dir = facing
        logger.info("Initializing agent's internal state of motion")

    def update_sensors(self):
        pos = self.clientinfo.position
        # discretize the absolute position and direction
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        cur_pos = Vector3(x, y, z)
        cur_dir = mvu.get_nearest_direction(pos.yaw)
        # update absolute state and current movement primitive
        delta_pos = mvu.get_nearest_delta_pos(self.state.pos, cur_pos)
        self.motion.delta_pos = motion_labels[delta_pos]
        delta_dir = mvu.get_nearest_delta_dir(self.state.dir, cur_dir)
        self.motion.delta_dir = motion_labels[delta_dir]
        self.state.pos = cur_pos
        self.state.dir = cur_dir
        #print("delta pos: {}, delta dir: {}".format(delta_pos, delta_dir))
        mvu.log_agent_motion(self.motion)
        mvu.log_agent_state(self.state)
