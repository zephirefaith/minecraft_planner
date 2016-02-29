import logging
import math

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from test_room_plugin import TestRoomPlugin
from utils.constants import *
import utils.movement_utils as mvu

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

# probably make this a subclass of some generic agent state
class AgentMovementState:
    def __init__(self, pos=None, facing=None, moving=None, turning=None):
        # x, y, z integer only
        self.pos = Vector3(*pos) if pos else None
        # cardinal directions only
        self.dir = facing
        # if the agent is moving or turning
        self.moving = moving
        self.turning = turning


@pl_announce('AtomicOperators')
class AtomicOperatorsPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World', 'Movement',
                'Inventory', 'Interact',
    )

    events = {
        'movement_position_reset':  'handle_position_reset',
        'movement_path_done':       'handle_path_done',
    }


    def __init__(self, ploader, settings):
        super(AtomicOperatorsPlugin, self).__init__(ploader, settings)

        # timer to update the agent's knowledge of its own movement
        frequency = FREQUENCY
        self.timers.reg_event_timer(frequency, self.sensor_timer_tick)


    #########################################################################
    # Egocentric movement operators
    #########################################################################

    def operator_move(self):
        # forward one unit/block, direction agent is facing
        pass

    def operator_look_left(self):
        pass

    def operator_look_right(self):
        pass

    # below functions are not yet implemented.
    # will have to create percepts for each of these as well
    def operator_check_inventory(self):
        # TODO: check inventory for list of items we currently have
        # return list of items
        pass

    def operator_check_inventory_for(self, material):
        # TODO: check inventory for particular object
        # return True or False
        pass

    def operator_check_holding(self):
        # TODO: check what we are currently holding
        # return identifier for this object.
        # (do we need unique IDs? or will generic material IDs suffice?)
        pass

    def operator_dig_block(self):
        # TODO: dig/gather the block where agent is currently facing
        # returns nothing
        pass

    def operator_place_block(self):
        # TODO: place a block where agent is currently facing
        # returns nothing
        pass

    #########################################################################
    # Allocentric movement operators
    #########################################################################
    def operator_move_to(self, x, y, z):
        pass

    def operator_move_to(self, thing):
        pass

    def operator_look_at(self, thing):
        pass

    def operator_dig_block_at(self, x, y, z):
        pass

    def operator_place_block_at(self, x, y, z):
        pass


    #########################################################################
    # Unclassified movement operators
    #########################################################################
    def operator_move_reset(self):
        # possibly reset facing position to NORTH
        pass

    def operator_turn_to(self, dir):
        # a compass direction.
        # is this allocentric, or not quite?
        pass

    #########################################################################
    # Utility functions for updating personal state
    #########################################################################
    def get_nearest_direction(self, yaw):
        deg_from = [(abs(NORTH - yaw),'NORTH'),
                    (abs(SOUTH - yaw),'SOUTH'),
                    (abs(WEST - yaw), 'WEST'),
                    (abs(EAST - yaw), 'EAST'),]
        diff,facing = min(deg_from)
        logger.debug("facing {} with a deviation of {}".format(facing, diff))
        return facing


    def get_nearest_position(self, x, y, z):
        pos = (math.floor(x),math.floor(y),math.floor(z))
        logger.debug("at position {} with original {}".format(pos, (x,y,z)))
        return pos


    def is_turning(self):
        if self.absolute_dir is None:
            return False

        diff = abs(self.absolute_dir - self.clientinfo.position.yaw)
        if diff > EPSILON_DIR:
            return True
        return False


    def is_moving(self):
        if self.absolute_pos is None:
            return False

        dist = math.sqrt(
            (self.absolute_pos.x - self.clientinfo.position.x)**2 +
            (self.absolute_pos.y - self.clientinfo.position.y)**2 +
            (self.absolute_pos.z - self.clientinfo.position.z)**2)
        if dist > EPSILON_DIST:
            return True
        return False


    def log_agent_state(self, agent_state):
        logger.info(
            "current state:\n<x:{}, y:{}, z:{}, facing:{}, moving:{}, turning:{}>\n".format(
                agent_state.pos.x,
                agent_state.pos.y,
                agent_state.pos.z,
                agent_state.facing,
                agent_state.moving,
                agent_state.turning,)
        )
