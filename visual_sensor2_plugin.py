import logging
import copy
import time

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from utils.constants import *
import utils.movement_utils as mov
from utils.camera_utils2 import FovUtils

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


@pl_announce('VisualSensor2')
class VisualSensor2Plugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World')

    events = {
        'client_join_game':     'handle_client_join',
        'sensor_tick_vision':   'handle_camera_tick',
    }

    def __init__(self, ploader, settings):
        super(VisualSensor2Plugin, self).__init__(ploader, settings)
        # not sure if this actually initializes the dict ahead of time...
        self.fov = FovUtils(max_dist=10)

    def handle_camera_tick(self, name, data):
        start = time.time()
        blocks_percept = self.get_visible_blocks(data)
        end = time.time()
        print("total ms for camera tick: {}".format(1000*(end-start)))
        self.draw_percept(blocks_percept)
        #logger.info("visual percept: {}".format(blocks_percept))
        print("visual percept: ")
        # for item in blocks_percept:
        #     print("{} : {}".format(item, blocks_percept[item]))
        self.event.emit('agent_visual_percept', blocks_percept)

    def handle_client_join(self, name, data):
        pass

    def get_visible_blocks(self, data):
        self.fov.set_cur_pos(data['x'], data['y'], data['z'], data['pitch'], data['yaw'])
        rel_coords = self.fov.get_rel_fov()
        blocked = set()
        visible = {coord:None for coord in rel_coords}
        for h,d in rel_coords:
            if (h,d) not in blocked:
                ax,ay,az = self.fov.rel_to_abs(h,d)
                block_id,block_meta = self.world.get_block(ax,ay,az)
                visible[(h,d)] = block_id
                if self.fov.is_solid(block_id):
                    blocked |= self.fov.get_blocked(h,d)

        return visible

    def draw_percept(self, visual_percept):
        coords = self.fov.get_rel_fov()
        max_dist = self.fov.max_dist
        print("__"*max_dist*2)
        for i in reversed(range(max_dist)):
            cur_list = [" "]*(max_dist*2 - 1)
            cur_coords = [(h,d) for h,d in coords if d == i]
            cur_blocked = [(h,d) for h,d in visual_percept if d == i and visual_percept[(h,d)] is None]
            cur_solid = [(h,d) for h,d in visual_percept if d == i and visual_percept[(h,d)] != 0 and visual_percept[(h,d)] != None]
            #print("blocked")
            for h,d in cur_blocked:
                #print("h: {}".format(h))
                cur_list[h+(max_dist-1)] = "-"
            #print("solid")
            for h,d in cur_solid:
                #print("h: {}".format(h))
                cur_list[h+(max_dist-1)] = "#"
            full_string = "|"
            for ch in cur_list:
                full_string += (ch + "|")
            print(full_string)
        print("__"*max_dist*2)
