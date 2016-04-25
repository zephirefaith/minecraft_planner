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
        'client_join_game':     'handle_client_join',
        'sensor_tick_vision':   'handle_camera_tick',
    }

    def __init__(self, ploader, settings):
        super(VisualSensorPlugin, self).__init__(ploader, settings)
        # initializes percept and precomputes all rays and block 'shadows'
        # most important line of code for performance
        self.fov = FovUtils(self.world, max_dist=10)

    def handle_camera_tick(self, name, data):
        #start = time.time()
        blocks_percept = self.get_visible_blocks(data)
        #end = time.time()
        #print("total ms for camera tick: {}".format(1000*(end-start)))
        self.draw_visual_percept(blocks_percept)
        #logger.info("visual percept: {}".format(blocks_percept))
        self.event.emit('agent_visual_percept', blocks_percept)

    def handle_client_join(self, name, data):
        pass

    def get_visible_blocks(self, data):
        visible = self.fov.update_percept(data)
        return visible

    def draw_visual_percept(self, percept):
        coords = self.fov.rel_fov
        max_dist = self.fov.max_dist
        print("visual percept: ")
        print("__"*max_dist*2)
        for i in reversed(range(max_dist)):
            cur_list = [" "]*(max_dist*2 - 1)
            full_string = "|"
            cur_coords = [(h,d) for h,d in coords
                if d == i]
            cur_blocked = [(h,d) for h,d in percept
                if (d == i and percept[(h,d)] is None)]
            cur_solid = [(h,d) for h,d in percept
                if (d == i and percept[(h,d)] != 0 and percept[(h,d)] != None)]

            for h,d in cur_blocked:
                cur_list[h+(max_dist-1)] = "-"
            for h,d in cur_solid:
                cur_list[h+(max_dist-1)] = "#"
            for ch in cur_list:
                full_string += (ch + "|")

            print(full_string)
        print("__"*max_dist*2)
