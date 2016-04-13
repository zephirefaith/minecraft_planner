import logging
import copy

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from utils.constants import *
import utils.movement_utils as mov
import utils.camera_utils as cam

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

# tick frequency for movement sensor
FREQUENCY = 1

# probably make this a subclass of some generic agent state
"""
class AgentMovementPrimitive(hop.State):
    def __init__(self, delta_pos=None, delta_dir=None):
        # movement is forward or none. faster movement is simply higher freq
        self.delta_pos = delta_pos if delta_pos else motion_labels[MOVE_NONE]
        # a turn is left, right or none
        self.delta_dir = delta_dir if delta_dir else motion_labels[TURN_NONE]

class AgentAbsoluteState:
    def __init__(self, abs_pos=None, abs_dir=None):
        # A Vector3 of (x,y,z) coordinates
        self.pos = abs_pos if abs_pos else None
        # compass direction in Minecraft yaw angle values
        self.dir = abs_dir if abs_dir else None
"""

@pl_announce('VisualSensor')
class VisualSensorPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World')

    events = {
        'client_join_game':     'handle_client_join',
        'sensor_tick_camera':   'handle_camera_tick',
    }

    def __init__(self, ploader, settings):
        super(VisualSensorPlugin, self).__init__(ploader, settings)
        # not sure if this actually initializes the dict ahead of time...
        cam.init_block_mats()
        #frequency = FREQUENCY
        #self.timers.reg_event_timer(frequency, self.camera_timer_tick)

    def handle_camera_tick(self, name, data):
        percept = self.handle_update_camera(data)
        logger.info("sending visual percept: {}".format(percept))
        self.event.emit('agent_visual_percept', percept)

    def handle_client_join(self, name, data):
        pass

    def handle_update_camera(self, data):
        # all block coordinates in the FOV cone (ignoring visibility)
        coords = cam.get_coordinates_in_range(data)
        #print("coordinates: {}".format(coords))
        # the actual block types given the world, at those locations
        blocks = self.get_block_multi(coords)
        #print("blocks: {}".format(blocks))
        vis_blocks = cam.get_visible_blocks(blocks)

        mov.log_agent_vision(vis_blocks)
        return vis_blocks

    def get_block_multi(self, coords):
        blocks = list()
        for pos in coords:
            data = copy.copy(pos)
            data['id'], data['meta'] = self.world.get_block(data['x'], data['y'], data['z'])
            blocks.append(data)
        return blocks

    def blocks_to_percept(self, blockslist):
        pos = self.clientinfo.position
        x,y,z = (pos.x, pos.y, pos.z)

        for block in blockslist
