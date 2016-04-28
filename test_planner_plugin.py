import logging
import copy
import math
import time

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

ACTION_TICK_FREQUENCY = 1.0

@pl_announce('TestPlanner')
class TestPlannerPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'AtomicOperators', 'Interact',
                'World', 'TestRoom', 'PerceptMonitor')

    events = {
        'world_block_update':       'handle_block_update',
        #'client_join_game':         'handle_client_join',
        'agent_planning_complete':  'register_execution_timer',
        #'agent_planning_failed':   'register_repair_timer',
    }

    def __init__(self, ploader, settings):
        super(TestPlannerPlugin, self).__init__(ploader, settings)
        self.init_planner()
        self.init_operators()
        ploader.provides('TestPlanner', self)

    def init_planner(self):
        logger.info("adding atomic operators to pyhop")
        self.init_state()
        # note: can call declare_operators multiple times for current situation
        hop.declare_operators(
            self.move_forward,
            self.turn_left,
            self.turn_right,
            self.break_block)
        hop.print_operators(hop.get_operators())
        # for the main task
        hop.declare_methods('get_resource', self.get_resource)
        # for each sub-task of the main task
        hop.declare_methods('find_route', self.find_route_to_resource)
        hop.declare_methods('navigate', self.navigate_to_resource)
        hop.declare_methods('acquire', self.acquire_resource)
        hop.print_methods(hop.get_methods())

    def init_state(self):
        # set state variables to be used by operators and methods
        self.state = hop.State('start_state')
        self.state.gold = 1 # 1: unbroken, 0: broken
        self.state.path = []
        self.state.gold_reached = 0
        self.state.path_found = 0
        self.state.path_idx = -1
        self.state.gold_broken = 0
        self.state.gold_acquired = 0

    def init_operators(self):
        self.op_translations = {
            'move_forward': self.atomicoperators.operator_move,
            'turn_left': self.atomicoperators.operator_look_left,
            'turn_right': self.atomicoperators.operator_look_right,
            'break_block': self.atomicoperators.operator_break_obstacle,}

    def register_execution_timer(self, name, data):
        self.timers.reg_event_timer(ACTION_TICK_FREQUENCY, self.execution_tick)

    def execution_tick(self):
        if not self.room_plan:
            print("no plan to execute")
            return
        plan_op = self.room_plan[self.plan_idx][0]
        self.op_translations[plan_op]()
        self.plan_idx += 1
        if self.plan_idx == len(self.room_plan):
            self.room_plan = []
            self.init_state()

    def handle_block_update(self, name, data):
        # gold block spawned in world. call the planner
        if data['block_data'] >> 4 == 41:
            pos = self.clientinfo.position
            self.state.start_loc = mvu.get_nearest_position(pos.x, pos.y, pos.z)
            self.state.current_position = self.state.start_loc
            self.state.current_orientation = mvu.get_nearest_direction(pos.yaw)

            block_pos = data['location']
            self.state.goal_loc = (block_pos['x'], block_pos['y'], block_pos['z'])

            self.solve()

            if self.room_plan is not None and len(self.room_plan) > 0:
                logger.info("plan succeeded")
                logger.info("total room plan: {}".format(self.room_plan))
                self.event.emit("agent_planning_complete")
                self.plan_idx = 0
            else:
                logger.info("plan failed")
                self.event.emit("agent_planning_failed")

    def solve(self):
        start = time.time()
        self.room_plan = hop.plan(self.state,
                            [('get_resource',)],
                            hop.get_operators(),
                            hop.get_methods(),
                            verbose=1)
        end = time.time()
        print("******* total time for planning: {} ms*******".format(1000*(end-start)))

    #########################################################################
    # operators
    #########################################################################

    def move_forward(self, state):
        #state = copy.deepcopy(state)
        x,y,z = state.current_position
        if (state.current_orientation == DIR_NORTH):
            state.current_position = (x,y,z-1)
        if (state.current_orientation == DIR_EAST):
            state.current_position = (x+1,y,z)
        if (state.current_orientation == DIR_SOUTH):
            state.current_position = (x,y,z+1)
        if (state.current_orientation == DIR_WEST):
            state.current_position = (x-1,y,z)
        return state

    def turn_left(self, state):
        state = copy.deepcopy(state)
        state.current_orientation = look_left_deltas[state.current_orientation]
        return state

    def turn_right(self, state):
        state = copy.deepcopy(state)
        state.current_orientation = look_right_deltas[state.current_orientation]
        return state

    def break_block(self, state):
        state = copy.deepcopy(state)
        if(state.gold == 1):
            state.gold = 0
            return state
        return False

    #########################################################################
    # methods
    #########################################################################
    # main task method. currently only way to get the resource
    def get_resource(self, state):
        print("calling get_resource")
        return [('find_route',),('navigate',),('acquire',)]

    def find_route_to_resource(self, state):
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
        print("calling navigate with state: {}".format(state.__name__))
        if state.path_idx == (len(state.path) - 1):
            state.gold_reached = 1
            return []
        if state.path_found == 1 and state.gold_reached == 0:
            cur_x,cur_y,cur_z = state.current_position
            next_x,next_y,next_z = state.path[state.path_idx]
            if next_x > cur_x:
                if state.current_orientation == DIR_EAST:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_left',), ('navigate',)]
            elif next_x < cur_x:
                if state.current_orientation == DIR_WEST:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_left',), ('navigate',)]
            elif next_z > cur_z:
                if state.current_orientation == DIR_SOUTH:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_left',), ('navigate',)]
            elif next_z < cur_z:
                if state.current_orientation == DIR_NORTH:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('navigate',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_left',), ('navigate',)]
            return []
        else:
            return False

    def acquire_resource(self, state):
        #state = copy.deepcopy(state)
        print("calling acquire with state: {}".format(state.__name__))
        if state.gold_acquired == 1:
            return []
        if state.gold_reached == 1 and state.gold_broken == 0:
            #gold block is unbroken
            #face the block, if already facing then break the block
            cur_x,cur_y,cur_z = state.current_position
            next_x,next_y,next_z = state.path[state.path_idx]
            if next_z < cur_z:
                if state.current_orientation == DIR_NORTH:
                    state.gold_broken = 1
                    return [('break_block',), ('acquire',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_left',), ('acquire',)]
            if next_z > cur_z:
                if state.current_orientation == DIR_SOUTH:
                    state.gold_broken = 1
                    return [('break_block',), ('acquire',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_left',), ('acquire',)]
            if next_x < cur_x:
                if state.current_orientation == DIR_WEST:
                    state.gold_broken = 1
                    return [('break_block',), ('acquire',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_left',), ('acquire',)]
            if next_x > cur_x:
                if state.current_orientation == DIR_EAST:
                    state.gold_broken = 1
                    return [('break_block',), ('acquire',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_left',), ('acquire',)]
            return []
        else:
            # gold block is broken, but not yet acquired
            state.gold_acquired = 1
            return [('move_forward',), ('acquire',)]
