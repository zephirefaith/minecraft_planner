import logging

# from spockbot.mcdata import blocks
# from spockbot.plugins.base import PluginBase, pl_announce
# from spockbot.plugins.tools.event import EVENT_UNREGISTER
# from spockbot.vector import Vector3

from utils.constants import *
#import utils.movement_utils as mvu

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

class PerceptUtils:
    def __init__(self):
        #super(PerceptMonitorPlugin, self).__init__(ploader, settings)
        #
        # self.visual = None
        # self.motion = None
        # self.inventory = None
        # self.mental_field = None
        # self.mental_action = None
        # self.percept_vector = None

    def linearize_visual_percept(self, percept):
        

    def linearize_motion_percept(self, name, data):
        logger.debug("received action percept: {}".format(data))
        self.action_percept = data

    def linearize_inventory_percept(self, name, data):
        logger.debug("received inventory percept: {}".format(data))

    # TODO: figure out if this is actually necessary
    # maybe can be compared just inside the planner?
    def linearize_mental_field_percept(self, name, data):
        logger.debug("received mental field percept: {}".format(data))

    def linearize_mental_action_percept(self, name, data):
        logger.debug("received mental action percept: {}".format(data))
