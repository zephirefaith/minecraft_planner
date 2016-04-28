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

@pl_announce('WallPlanner')
class WallPlannerPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'AtomicOperators', 'Interact',
                'World', 'TestRoom', 'PerceptMonitor')

    events = {
        'world_block_update':       'handle_block_update',
        #'client_join_game':         'handle_client_join',
        'agent_planning_complete':  'register_execution_timer',
        #'agent_planning_failed':   'register_repair_timer',
    }

    def __init__(self, ploader, settings):
        super(WallPlannerPlugin, self).__init__(ploader, settings)
        self.init_planner()
        self.init_operators()
        ploader.provides('WallPlanner', self)

    def init_planner(self):
        logger.info("adding atomic operators to pyhop")
        self.init_state()
        # note: can call declare_operators multiple times for current situation
        hop.declare_operators(
            self.move_forward,
            self.turn_left,
            self.turn_right,
            self.break_block,
            self.equip_agent)
        hop.print_operators(hop.get_operators())
        # for the main task
        hop.declare_methods('get_resource', self.get_resource)
        # for each sub-task of the main task
        hop.declare_methods('find_route', self.find_route)
        hop.declare_methods('navigate', self.navigate)
        hop.declare_methods('acquire', self.acquire_resource)
        hop.declare_methods('break_wall', self.break_wall)
        hop.print_methods(hop.get_methods())

    def init_state(self):
        # set state variables to be used by operators and methods
        self.state = hop.State('start_state')

        self.state.path = []
        self.state.path_found = 0
        self.state.path_idx = -1
        self.state.targets = {
            'gold': {
                'location': (0,0,0),
                'reached': 0,
                'broken': 0,
                'acquired': 0,
            },
            'wall': {
                'location': (-66,14,-46),
                'reached': 0,
                'broken': 0,
            },
        }
        # variables for wall-in-the-room scenario
        self.state.inventory = { #availability of materials to our agent
            'wood' : 1,
            'iron' : 0,
            'steel' : 1,
        }
        self.state.equipment = None
        #self.state.equipped = 0     # 0: no equipment in hand, 1: equipped with tool

        self.preconditions = {
            'break_wall' : {
                'precondition'  : None,
                'inventory'     : 'iron',
            },
        }

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
            self.state.targets['gold']['location'] = (
                block_pos['x'],
                block_pos['y'],
                block_pos['z'])

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
                            verbose=3)
        end = time.time()
        print("******* total time for planning: {} ms*******".format(1000*(end-start)))

    #########################################################################
    # operators
    #########################################################################

    def move_forward(self, state):
        x,y,z = state.current_position
        if (state.current_orientation == DIR_NORTH):
            state.current_position = (x,y,z-1)
        if (state.current_orientation == DIR_EAST):
            state.current_position = (x+1,y,z)
        if (state.current_orientation == DIR_SOUTH):
            state.current_position = (x,y,z+1)
        if (state.current_orientation == DIR_WEST):
            state.current_position = (x-1,y,z)
        if (state.current_position.y - state.wall_location.y) <= 1:
            state.wall_reached = 1
        return state

    def turn_left(self, state):
        state.current_orientation = look_left_deltas[state.current_orientation]
        return state

    def turn_right(self, state):
        state.current_orientation = look_right_deltas[state.current_orientation]
        return state

    def break_block(self, state):
        if state.wall_reached == 1 and state.wall_state == 1:
            if state.equipment == 'iron' or state.equipment == 'steel':
                state.wall_state = 0
                return state
        if state.wall_state == 0 and state.gold == 1:
            state.gold = 0
            return state
        return False

    def equip_agent(self, state, materials):
        # check if the materials required are available in inventory to be
        # equipped or not
        material = None
        for sample in materials:
            if state.inventory[sample] == 1:
                material = sample
                break

        if material is None:
            return False
        else:
            state.equipment = sample
            state.equipped = 1
            return state

    #########################################################################
    # methods
    #########################################################################
    # main task method. currently only way to get the resource
    def get_resource(self, state):
        print("calling get_resource")

        return [('find_route', 'wall'), ('navigate','wall'),('break_wall',), ('find_route', 'gold'), ('navigate','gold'), ('acquire',)]

    def find_route(self, state, target):
        print("calling find_route with target: {}".format(target))
        state.path_found = 0
        #state.subgoal = target
        state.path = self.testroom.compute_path(state.current_position, state.targets[target]['location'])
        print("current path: {}".format(state.path))
        if not state.path:
            return False
        else:
            state.path_found = 1
            state.path_length = len(state.path)
            state.path_idx = 0
        return []

    def navigate(self, state, target):
        print("calling navigate with target: {}".format(target))
        if state.path_idx == (len(state.path) - 1):
            state.targets[target]['reached'] = 1
            return []
        if state.path_found == 1 and state.targets[target]['reached'] == 0:
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
        if state.targets['gold']['acquired'] == 1:
            return []
        if (state.targets['gold']['reached'] == 1 and
            state.targets['gold']['broken'] == 0):
            #gold block not yet broken
            #face the block, if already facing then break the block
            cur_x,cur_y,cur_z = state.current_position
            next_x,next_y,next_z = state.path[state.path_idx]
            if next_z < cur_z:
                if state.current_orientation == DIR_NORTH:
                    state.targets['gold']['broken'] = 1
                    return [('break_block',), ('acquire',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_left',), ('acquire',)]
            if next_z > cur_z:
                if state.current_orientation == DIR_SOUTH:
                    state.targets['gold']['broken'] = 1
                    return [('break_block',), ('acquire',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_left',), ('acquire',)]
            if next_x < cur_x:
                if state.current_orientation == DIR_WEST:
                    state.targets['gold']['broken'] = 1
                    return [('break_block',), ('acquire',)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('acquire',)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_left',), ('acquire',)]
            if next_x > cur_x:
                if state.current_orientation == DIR_EAST:
                    state.targets['gold']['broken'] = 1
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
            state.targets['gold']['acquired'] = 1
            return [('move_forward',), ('acquire',)]

    def break_wall(self, state):
        tool = self.preconditions['break_wall']['inventory']

        # check preconditions:
        if state.inventory[tool] == 0:
            return False
        # if wall hasn't been reached at this point, method fails
        if state.targets['wall']['reached'] == 0:
            return False

        # actual method execution
        if state.equipment is None:
            return [('equip_agent', tool),('break_wall',)]
        elif state.targets['wall']['broken'] == 0:
            return [('break_block',)]
        return False
