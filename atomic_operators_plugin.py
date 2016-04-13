import logging
import copy

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from test_room_plugin import TestRoomPlugin
from utils.constants import *
import utils.movement_utils as mvu

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


@pl_announce('AtomicOperators')
class AtomicOperatorsPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'Movement', 'Interact',)

    events = {
        # 'movement_position_reset':  'handle_position_reset',
        # 'movement_path_done':       'handle_path_done',
    }

    def __init__(self, ploader, settings):
        super(AtomicOperatorsPlugin, self).__init__(ploader, settings)
        ploader.provides('AtomicOperators',self)

    #########################################################################
    # Egocentric movement operators
    #########################################################################

    def operator_move(self):
        print("calling operator move")
        # forward one unit/block, direction agent is facing
        pos = self.clientinfo.position
        facing = mvu.get_nearest_direction(pos.yaw)
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        x,y,z = move_deltas[facing](x,y,z)
        self.movement.move_to(x,y,z)


    def operator_look_left(self):
        print("calling operator look left")
        facing = mvu.get_nearest_direction(self.clientinfo.position.yaw)
        new_facing = look_left_deltas[facing]
        self.interact.look(yaw=new_facing,pitch=0.0)


    def operator_look_right(self):
        print("calling operator look right")
        facing = mvu.get_nearest_direction(self.clientinfo.position.yaw)
        new_facing = look_right_deltas[facing]
        self.interact.look(yaw=new_facing,pitch=0.0)

    def operator_break_obstacle(self):
        print("calling operator break obstacle")
        pos = copy.deepcopy(self.clientinfo.position)
        facing = mvu.get_nearest_direction(pos.yaw)
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        target_block_coords = move_deltas[facing](x,y,z)
        #print("target block integer coords: {}".format(target_block_coords))
        target_block_center = tuple([cb+0.5 for cb in target_block_coords])
        #print("target block center coords: {}".format(target_block_center))
        pos.yaw = facing
        pos.pitch = 0.0
        pos.x,pos.y,pos.z = target_block_coords
        self.interact.dig_block(pos)
        self.interact.look(yaw=facing,pitch=0.0)



    def operator_place_block(self):
        # TODO: place a block where agent is currently facing
        # returns nothing
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

    #########################################################################
    # Allocentric movement operators
    #########################################################################

    # sort of a "cheat" move command. will invoke Spock pathfinding
    # this really shouldn't be used except for special cases
    def operator_move_to(self, x, y, z):
        self.movement.move_to(x,y,z)

    # TODO: **cannot be implemented yet**
    # need some notion of an 'object' in the world,
    # which will have coordinates associated with it
    #def operator_move_to(self, thing):
    #    pass

    #def operator_look_at(self, thing):
    #    pass

    def operator_dig_block_at(self, x, y, z):
        pass

    def operator_place_block_at(self, x, y, z):
        pass


    #########################################################################
    # Unclassified movement operators
    #########################################################################
    def operator_move_reset(self):
        # simply centers the agent and sets look direction to NORTH
        pos = self.clientinfo.position
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        self.interact.look(yaw=DIR_NORTH, pitch=0.0)
        self.movement.move_to(x,y,z)


    def operator_turn_to(self, facing):
        # a compass direction.
        # is this allocentric, or not quite?
        new_facing = mvu.get_nearest_direction(facing)
        self.interact.look(yaw=new_facing, pitch=0.0)
