import logging
import copy
import time

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from utils.constants import *
import utils.movement_utils as mov
from utils.camera_utils import FovUtils

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


@pl_announce('VisualSensor')
class VisualSensorPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World')

    events = {
        #'client_join_game':     'handle_client_join',
        'sensor_tick_vision':   'handle_camera_tick',
    }

    def __init__(self, ploader, settings):
        super(VisualSensorPlugin, self).__init__(ploader, settings)
        # initializes percept and precomputes all rays and block 'shadows'
        # most important line of code for performance
        self.fov = FovUtils(self.world, max_dist=10)
        #ploader.provides('VisualSensor', self)

    def handle_camera_tick(self, name, data):
        blocks_percept = self.get_visible_blocks(data)
        #logger.debug("current visual percept: {}".format(blocks_percept))
        self.fov.draw_visual_percept(blocks_percept['blocks'])
        self.event.emit('agent_visual_percept', blocks_percept)

    def get_visible_blocks(self, data):
        #start = time.time()
        coords = self.fov.rel_fov
        visible = self.fov.update_percept(data)
        percept = {
            'coords': coords,
            'blocks': visible,
        }
        #end = time.time()
        #print("total time for camera tick: {} ms".format(1000*(end-start)))
        return percept
