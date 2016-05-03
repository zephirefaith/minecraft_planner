import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

import utils.movement_utils as mvu
PERCEPT_REQUEST_FREQUENCY = 1

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

@pl_announce('VisualPlanner')
class VisualPlannerPlugin(PluginBase):
    requires = ('Event', 'Timers', 'ClientInfo', 'VisualSensorPlugin')

    events = {
        'client_join_game': 'handle_client_join',
        'agent_visual_percept': 'handle_visual_percept',
    }

    def __init__(self, ploader, settings):
        super(VisualPlannerPlugin, self).__init__(ploader, settings)
        self.visual_percept = None
        self.timers.reg_event_timer(PERCEPT_REQUEST_FREQUENCY, self.percept_request_tick)

    def handle_client_join(self, name, data):
        pos = self.clientinfo.position
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        orientation = mvu.get_nearest_direction(pos.yaw)
        self.request_visual_percept(x, z, orientation)

    def percept_request_tick(self):
        pos = self.clientinfo.position
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        orientation = mvu.get_nearest_direction(pos.yaw)
        self.request_visual_percept(x, z, orientation)

    def request_visual_percept(self, x, z, orientation):
        data = {
            'x':x,
            'y':13,
            'z':z,
            'pitch':0,
            'yaw':orientation,
        }
        logger.debug("sending request with data: {}".format(data))
        self.event.emit('sensor_tick_vision', data)

    def handle_visual_percept(self, name, data):
        logger.debug("handling percept: {}".format(data))
        self.visual_percept = data
