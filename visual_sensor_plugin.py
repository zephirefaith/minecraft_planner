import logging
import copy
import time

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from utils.constants import *
import utils.movement_utils as mov
import utils.camera_utils as cam

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


@pl_announce('VisualSensor')
class VisualSensorPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World')

    events = {
        'client_join_game':     'handle_client_join',
        'sensor_tick_vision':   'handle_camera_tick',
    }

    def __init__(self, ploader, settings):
        super(VisualSensorPlugin, self).__init__(ploader, settings)
        # not sure if this actually initializes the dict ahead of time...
        cam.init_block_mats()

    def handle_camera_tick(self, name, data):
        start = time.time()
        blocks_percept = self.get_visible_blocks(data)
        relative_percept = self.percept_to_relative(blocks_percept)
        end = time.time()
        print("total ms for camera tick: {}".format(1000*(end-start)))
        logger.info("visual percept: {}".format(blocks_percept))
        logger.info("relative visual percept: {}".format(relative_percept))
        self.event.emit('agent_visual_percept', relative_percept)

    def handle_client_join(self, name, data):
        pass

    def get_visible_blocks(self, data):
        # all block coordinates in the FOV cone (ignoring visibility)
        coords = cam.get_coordinates_in_range(data)
        #print("coordinates: {}".format(coords))
        # the actual block types given the world, at those locations
        blocks = self.get_block_multi(coords)
        #print("blocks: {}".format(blocks))
        vis_blocks = cam.get_visible_blocks(blocks)
        #mov.log_agent_vision(vis_blocks)
        return vis_blocks

    def get_block_multi(self, coords):
        blocks = list()
        for pos in coords:
            data = copy.copy(pos)
            data = dict()
            data['coords'] = (pos['x'],pos['y'],pos['z'])
            data['id'], data['meta'] = self.world.get_block(*data['coords'])
            blocks.append(data)
        return blocks

    def percept_to_relative(self, percept):
        pos = self.clientinfo.position
        pos_coords = mov.get_nearest_position(pos.x, pos.y, pos.z)
        rel_percept = dict()
        for xyz in percept:
            rel_coords = tuple([p1-p0 for p0,p1 in zip(pos_coords,xyz)])
            rel_percept[rel_coords] = percept[xyz]
        return rel_percept
