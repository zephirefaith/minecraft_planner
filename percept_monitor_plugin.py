import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from utils.constants import *
import utils.movement_utils as mvu
import utils.perception_utils as pcu

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


class PerceptMonitorCore(object):
    def __init__(self, monitor):
        self.monitor = monitor

    def get_visual_percept(self):
        return self.monitor.visual

    def get_movement_percept(self):
        return self.monitor.motion


@pl_announce('PerceptMonitor')
class PerceptMonitorPlugin(PluginBase):
    requires = ('Event', 'Timers')
    events = {
        # FOV. list of coordinates and block ids
        'agent_visual_percept': 'handle_visual_percept',
        # physical action taken in the last motion perception timestep
        'agent_motion_percept':'handle_motion_percept',
        # what the agent currently 'has' on its body
        'agent_inventory_percept':'handle_inventory_percept',
        # the objects the agent is currently thinking about (WM?)
        'agent_mental_field_percept':'handle_mental_field_percept',
        # the mental action the agent is currently taking (about to take?)
        'agent_mental_action_percept':'handle_mental_action_percept',
    }

    def __init__(self, ploader, settings):
        super(PerceptMonitorPlugin, self).__init__(ploader, settings)

        self.visual = None
        self.motion = None
        self.inventory = None
        # self.mental_field = None
        # self.mental_action = None
        # self.percept_vector = None

        self.core = PerceptMonitorCore(self)
        self.p_utils = pcu.PerceptionUtils()
        # for the getter functions in PerceptMonitorCore
        ploader.provides('PerceptMonitor', self.core)

    def handle_visual_percept(self, name, data):
        logger.debug("received visual percept: {}".format(data))
        self.visual = data['blocks']
        ordering = data['coords']
        self.p_utils.linearize_visual_percept(self.visual, ordering)

    def handle_motion_percept(self, name, data):
        logger.debug("received motion percept: {}".format(data))
        self.motion = data['motion']
        ordering = data['ordering']
        self.p_utils.linearize_motion_percept(self.motion, ordering)

    def handle_inventory_percept(self, name, data):
        logger.debug("received inventory percept: {}".format(data))

    # TODO: figure out if this is actually necessary
    # maybe can be compared just inside the planner?
    def handle_mental_field_percept(self, name, data):
        logger.debug("received mental field percept: {}".format(data))

    def handle_mental_action_percept(self, name, data):
        logger.debug("received mental action percept: {}".format(data))
