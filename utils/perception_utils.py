import logging
import numpy as np

# from spockbot.mcdata import blocks
# from spockbot.plugins.base import PluginBase, pl_announce
# from spockbot.plugins.tools.event import EVENT_UNREGISTER
# from spockbot.vector import Vector3

from utils.constants import *
from utils.camera_utils import FovUtils
#import utils.movement_utils as mvu

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

class PerceptionUtils:
    def __init__(self):
        # a DefaultDict is probably better here
        self.block_types = {
            # unknown
            None:   '0',
            # air block. no data
            0:      '1',
            # gold block. resource
            41:     '2'
        }

        self.visual_vector = []
        self.motion_vector = []
        self.inventory_vector = []
        self.mental_field_vector = []
        self.mental_action_vector = []

        self.percept_vector = []

    def get_block_type(self, blockid):
        if blockid in self.block_types:
            return self.block_types[blockid]
        # the default type for all solid blocks
        return '3'

    def linearize_visual_percept(self, percept, percept_ordering):
        for h,d in percept_ordering:
            print("current coordinate: {}".format((h,d)))
        vp_list = self.get_block_type(percept[(h,d)] for h,d in percept_ordering)
        self.visual_vector = np.array(vp_list)
        print(self.visual_vector)



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
