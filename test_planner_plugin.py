import logging
import copy

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from pyhop import hop

from test_room_plugin import TestRoomPlugin, START_COORDS
from utils import movement_utils as mvu
from utils.constants import *

__author__ = 'Priyam Parashar'
logger = logging.getLogger('spockbot')

@pl_announce('TestPlanner')
class TestPlannerPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World', 'TestRoom')

    events = {
        'world_block_update':   'handle_block_update',
        'client_join_game':     'handle_client_join',
        #'movement_position_reset':  'handle_position_reset',
        #'movement_path_done':       'handle_path_done',
    }

    #orientation = {'N', 'E', 'S', 'W'}

    def __init__(self, ploader, settings):
        super(TestPlannerPlugin, self).__init__(ploader, settings)

        logger.info("adding atomic operators to pyhop:")
        # note: can call declare_operators multiple times for current situation
        hop.declare_operators(
            self.move_forward,
            self.turn_left,
            self.turn_right,
            self.break_block)
        hop.print_operators(hop.get_operators())

        # for the main task (so far only one option)
        hop.declare_methods(
            'get_resource',
            self.get_resource)

        # for each sub-task of the main task
        hop.declare_methods('find_route', self.find_route_to_resource)
        hop.declare_methods('navigate', self.navigate_to_resource)
        hop.declare_methods('acquire', self.acquire_resource)

        # methods will be nested
        # hop.declare_methods(
        #     'get_resource',
        #     self.find_route_to_resource,    # BFS() or A*
        #     self.navigate_to_resource,      # follow the path BFS spewed out
        #     self.acquire_resource)          # break the block and move move_forward
        hop.print_methods(hop.get_methods())

        # set state variables
        # will be used by operators and methods
        self.state = hop.State('start_state')
        #state.start_loc = self.start_location
        #state.goal_loc = self.gold_location
        self.state.gold = 1 # 1: unbroken, 0: broken
        self.state.path = []
        self.state.gold_reached = 0
        self.state.path_found = 0
        self.state.path_idx = -1
        self.state.gold_acquired = 0

        ploader.provides('TestPlanner', self)

    # must wait for client init event, or start coords will be (0,0,0)
    def handle_client_join(self, name, data):
        # necessary for position and orientation agent to be initialized
        pos = self.clientinfo.position

        self.state.start_loc = (pos.x, pos.y, pos.z)
        self.state.current_position = self.state.start_loc
        self.state.current_orientation = mvu.get_nearest_direction(pos.yaw)


    # block update handler to trigger the planner to start
    def handle_block_update(self, name, data):
        # there is a gold block. call the planner
        if data['block_data'] >> 4 == 41:
            # just re-initialize the start pos and angle
            pos = self.clientinfo.position
            self.state.start_loc = (pos.x, pos.y, pos.z)
            self.state.current_position = self.state.start_loc
            self.state.current_orientation = mvu.get_nearest_direction(pos.yaw)

            x = data['location']['x']
            y = data['location']['y']
            z = data['location']['z']
            self.state.goal_loc = (x, y, z)
            success = self.solve()
            print("total room plan: {}".format(self.room_plan))
            if success:
                print("plan succeeded")
            else:
                print("plan failed")

    def solve(self):
        self.room_plan = hop.plan(self.state,
                            [('get_resource',)],
                            hop.get_operators(),
                            hop.get_methods(),
                            verbose=3)
        if not self.room_plan:
            return False
        else:
            return True

    #############
    # operators #
    #############

    # assuming location to be (x,y)
    def move_forward(self, state):
        state = copy.deepcopy(state)
        if (state.current_orientation == DIR_NORTH):
            state.current_position[2] = state.current_position[2] - 1
        if (state.current_orientation == DIR_EAST):
            state.current_position[0] = state.current_position[0] + 1
        if (state.current_orientation == DIR_SOUTH):
            state.current_position[2] = state.current_position[2] + 1
        if (state.current_orientation == DIR_WEST):
            state.current_position[0] = state.current_position[0] - 1

        return state

    def turn_left(self, state):
        state = copy.deepcopy(state)
        #state.current_orientation = state.current_orientation + 1
        state.current_orientation = look_left_deltas[state.current_orientation]
        return state

    def turn_right(self, state):
        state = copy.deepcopy(state)
        #state.current_orientation = state.current_orientation - 1
        state.current_orientation = look_right_deltas[state.current_orientation]
        return state

    def break_block(self):
        state = copy.deepcopy(state)
        if(state.gold == 1):
            state.gold = 0
            return state
        return False

    ###########
    # methods #
    ###########
    # main task method. currently only way to get the resource
    def get_resource(self, state):
        state = copy.deepcopy(state)
        print("calling get_resource")
        return [('find_route',),('navigate',),('acquire',)]

    def find_route_to_resource(self, state):
        state = copy.deepcopy(state)
        print("calling find_route with state: {}".format(state.__name__))
        if not state.path:
            state.path = self.testroom.compute_path(state.current_position, state.goal_loc)
            if not state.path:
                return False
            else:
                state.path_found = 1
                state.path_length = len(state.path)
                state.path_idx = 0
        return []

    def navigate_to_resource(self, state):
        state = copy.deepcopy(state)
        print("calling navigate with state: {}".format(state.__name__))
        if state.path_found == 1 and state.gold_reached == 0:
            next_position = state.path[state.path_idx]
            if state.path_idx == (len(state.path) - 1):
                state.gold_reached == 1
                return False
            if next_position[0]>state.current_position[0]:
                if state.current_orientation == DIR_EAST:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_left',)]
            elif next_position[0]<state.current_position[0]:
                if state.current_orientation == DIR_WEST:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_left',)]
            elif next_position[2]>state.current_position[2]:
                if state.current_orientation == DIR_SOUTH:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_left',)]
            elif next_position[2]<state.current_position[2]:
                if state.current_orientation == DIR_NORTH:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_left',)]
        else:
            return False

    def acquire_resource(self, state):
        state = copy.deepcopy(state)
        print("calling find_route")
        if state.gold_reached == 1 and state.gold_acquired == 0:
            if state.gold == 1:
                #gold block is unbroken
                #face the block, if already facing then break the block
                if state.goal_loc[2]<state.current_position[2]:
                    if state.current_orientation == DIR_NORTH:
                        return [('break_block',)]
                    elif state.current_orientation == DIR_WEST:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_SOUTH:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_EAST:
                        return [('turn_left',)]
                if state.goal_loc[2]>state.current_position[2]:
                    if state.current_orientation == DIR_SOUTH:
                        return [('break_block',)]
                    elif state.current_orientation == DIR_EAST:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_NORTH:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_WEST:
                        return [('turn_left',)]
                if state.goal_loc[0]<state.current_position[0]:
                    if state.current_orientation == DIR_WEST:
                        return [('break_block',)]
                    elif state.current_orientation == DIR_EAST:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_SOUTH:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_NORTH:
                        return [('turn_left',)]
                if state.goal_loc[0]>state.current_position[0]:
                    if state.current_orientation == DIR_EAST:
                        return [('break_block',)]
                    elif state.current_orientation == DIR_WEST:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_NORTH:
                        return [('turn_right',)]
                    elif state.current_orientation == DIR_SOUTH:
                        return [('turn_left',)]

            else:
                state.gold_acquired = 1
                return [('move_forward',)]
        else:
            return False
