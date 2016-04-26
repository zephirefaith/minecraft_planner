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
        self.vectors = {
            'visual': np.array([]),
            'motion': np.array([]),
            'inventory': np.array([]),
        }
        self.vector_sizes = {
            'visual':   0,
            'motion':   0,
            'inventory':0,
        }
        self.vector_ordering = ['visual','motion','inventory',]
        self.combined_vector = np.array([])

    def get_block_type(self, blockid):
        if blockid in percept_types_block:
            return percept_types_block[blockid]
        # the default type for all solid blocks
        return '3'

    def linearize_visual_percept(self, percept, percept_ordering):
        # for h,d in percept_ordering:
        #     print("current coordinate: {}".format((h,d)))
        self.vectors['visual'] = np.array([self.get_block_type(percept[(h,d)])
            for h,d in percept_ordering])
        self.vector_sizes['visual'] = len(self.vectors['visual'])
        logger.debug("visual vector: \n{}".format(self.vectors['visual']))

    def linearize_motion_percept(self, percept, percept_ordering):
        self.vectors['motion'] = np.array([percept_types_motion[percept[key]]
            for key in percept_ordering])
        self.vector_sizes['motion'] = len(self.vectors['motion'])
        logger.debug("motion vector: {}".format(self.vectors['motion']))

    def linearize_inventory_percept(self, percept, percept_ordering):
        self.vectors['inventory'] = np.array([percept_types_inventory[percept[item]]
            for item in percept_ordering])
        self.vector_sizes['inventory'] = len(self.vectors['inventory'])
        logger.debug("inventory vector: {}".format(self.vectors['inventory']))

    def update_combined_vectors(self):
        cur_idx = 0
        for label in self.vector_ordering:
            cur_offset = cur_idx + self.vector_sizes[label]
            cur_vector = self.vectors[label]
            np.put(a=combined,ind=[cur_idx,cur_offset],v=cur_vector)
            cur_idx += self.vector_sizes[label]


    # # TODO: figure out if this is actually necessary
    # # maybe can be compared just inside the planner?
    # def linearize_mental_field_percept(self, name, data):
    #     logger.debug("received mental field percept: {}".format(data))
    #
    # def linearize_mental_action_percept(self, name, data):
    #     logger.debug("received mental action percept: {}".format(data))
