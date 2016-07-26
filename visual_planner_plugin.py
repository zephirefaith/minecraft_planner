import logging
import time

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from pyhop import hop

from test_room_plugin import TestRoomPlugin, START_COORDS
import utils.movement_utils as mvu
from utils.constants import *

ACTION_TICK_FREQUENCY = 1

#########################################################################
# information
#########################################################################

__author__ = ['Bradley Sheneman', 'Priyam Parashar']
logger = logging.getLogger('spockbot')

#########################################################################
# initialization
#########################################################################

@pl_announce('VisualPlanner')
class VisualPlannerPlugin(PluginBase):
    requires = ('Event', 'Timers', 'ClientInfo', 'AtomicOperators',
    'VisualSensorPlugin')

    events = {
        'client_join_game': 'handle_client_join',
        'agent_visual_percept': 'handle_visual_percept',
        'world_block_update': 'handle_block_update',
        'agent_planning_complete': 'register_execution_timer',
    }

    #########################################################################
    # plugin events
    #########################################################################

    def __init__(self, ploader, settings):
        super(VisualPlannerPlugin, self).__init__(ploader, settings)
        self.visual_percept = None
        self.init_planner()
        self.init_operators()
        ploader.provides('VisualPlanner', self)

    def handle_client_join(self, name, data):
        self.perceive()
        logger.info("List of blocks: {}".format(self.visual_percept['blocks']))

    def handle_block_update(self, name, data):
        # gold block spawned in world. call the planner
        if data['block_data'] >> 4 == 41:
            pos = self.clientinfo.position
            self.state.agent['start_xyz'] = mvu.get_nearest_position(pos.x, pos.y, pos.z)
            self.state.agent['cur_xyz'] = self.state.agent['start_xyz']
            self.state.agent['start_theta'] = mvu.get_nearest_direction(pos.yaw)
            self.state.agent['cur_theta'] = self.state.agent['start_theta']
            block_pos = data['location']
            self.perceive()
            for block in self.visual_percept['blocks']:
                print([block," ",self.visual_percept['blocks'][block]])
            # self.state.targets['gold']['location'] = (
            #     block_pos['x'],
            #     block_pos['y'],
            #     block_pos['z'])
            self.planner()
            # if self.room_plan is not None and len(self.room_plan) > 0:
            #     logger.info("plan succeeded")
            #     logger.info("total room plan: {}".format(self.room_plan))
            #     self.event.emit("agent_planning_complete")
            #     self.plan_idx = 0
            # else:
            #     logger.info("plan failed")
            #     self.event.emit("agent_planning_failed")

    def handle_visual_percept(self, name, data):
        logger.debug("handling percept: {}".format(data))
        self.visual_percept = data

    def perceive(self):
        pos = self.clientinfo.position
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        orientation = mvu.get_nearest_direction(pos.yaw)
        self.request_visual_percept(x, z, orientation)

    def request_visual_percept(self, x, z, orientation):
        data = {
            'x':x,
            'y':14,
            'z':z,
            'pitch':0,
            'yaw':orientation,
        }
        logger.debug("sending request with data: {}".format(data))
        self.event.emit('sensor_tick_vision', data)

    def register_execution_timer(self, name, data):
        self.timers.reg_event_timer(ACTION_TICK_FREQUENCY, self.metaplanner)

    def init_operators(self):
        self.op_translations = {
            'move_forward': self.atomicoperators.operator_move,
            'turn_left': self.atomicoperators.operator_look_left,
            'turn_right': self.atomicoperators.operator_look_right,
            'break_block': self.atomicoperators.operator_break_obstacle,}

    #########################################################################
    # planner knowledge base
    #########################################################################

    def init_planner(self):
        logger.info("adding atomic operators to pyhop")
        self.init_state()
        # note: can call declare_operators multiple times for current situation
        hop.declare_operators(
            self.move_forward,
            self.turn_left,
            self.turn_right,
            self.break_block)
        #    self.equip_agent)
        hop.print_operators(hop.get_operators())
        # for the main task
        hop.declare_methods('get_resource', self.get_resource)
        # for each sub-task of the main task
        hop.declare_methods('search_for_gold', self.search_for_gold)
        hop.declare_methods('move_closer', self.move_closer)
        hop.declare_methods('acquire_gold', self.acquire_resource)
        # hop.declare_methods('break_wall', self.break_wall)
        hop.print_methods(hop.get_methods())

    def init_state(self):
        # set state variables to be used by operators and methods
        self.state = hop.State('start_state')
        # TODO: convert everything into one directory which has 'resource', 'inventory' key all in one
        # variables in this minecraft world
        self.world_is_okay = None
        self.state.objects = {
            'gold',
            'stone_block',
        }
        self.state.object_id = [41, 100]
        self.state.tools = {}
        # information structure for keeping track of world state
        self.state.resources = {}
        for obj in self.state.objects:
            self.state.resources[obj] = {
                'state':        None,
                'hemisphere':   None,
                'location':     None,
            }
        # information structure to keep track of self state
        # State = None: not located yet, 0: seen but not near, 1: near, -1: broken
        # Hemisphere = None: Haven't seen so far, -1: was to the left of the cone,
        # 0: was in the center, +1: was to the right of the cone
        self.state.agent = {
            'cur_xyz':       None,
            'cur_theta':    None,
            'start_xyz':     None,
            'start_theta':  None,
        }
        self.state.inventory = {}
        for obj in self.state.objects:
            self.state.inventory[obj] = 0
        # self.state.need_percept = 0
        #goal state
        self.goal_state = hop.State('goal_state')
        self.goal_state.resources = {}
        self.goal_state.resources['gold'] = {
            'state': -1,
            'hemisphere': [-1,0,1],
        }
        self.goal_state.inventory = {}
        self.goal_state.inventory['gold'] = 1
        self.assertions = {}
        self.assertions = {
            1: {
                'resources': {
                    'gold': {
                        'state': 0,
                    },
                },
            },
            # gold must be in sight to plan how to navigate
            2: {
                'resources': {
                    'gold': {
                        'state': 1,
                    },
                },
            },
            # agent must be next to gold block to plan how to break it
        }

    #########################################################################
    # planner helper functions
    #########################################################################

    def continual_planner(self):
        # a function which executes returned plan, senses
        # percepts and decides if replanning should be done
        # get initial plan
        self.solve()
        if not self.room_plan:
            print("no plan to execute")
            return
        #start execution loop
        while self.world_is_okay == 1:
            self.execute()
            self.perceive()
            self.assertion_monitor()
        if self.world_is_okay is None:
            return

    def solve(self):
        start = time.time()
        self.room_plan = hop.plan(self.state,
                            [('get_resource',)],
                            hop.get_operators(),
                            hop.get_methods(),
                            verbose=1)
        end = time.time()
        print("******* total time for planning: {} ms*******".format(1000*(end-start)))
        print("result of hop.plan(): {}".format(self.room_plan))
        #print("last failed method label: {}".format(self.failed_method))

    def execute(self):
        # will basically just execute action represented at self.plan_idx index in the plan
        plan_op = self.room_plan[self.plan_idx][0]
        self.op_translations[plan_op]()
        self.plan_idx += 1
        return

    def assertion_monitor(self):
        # monitor --> replan if assertion is fulfilled
        # later --> compare and analyze expected VS actual state
        if self.plan_idx == len(self.room_plan):
            self.room_plan = []
            self.init_state()
        return False

    def check_assertion(self, assertion, state):
        # directories where assertions could be checked
        keys = ['resources', 'inventory']
        result = 1
        if keys[0] in assertion:
            for obj in assertion[keys[0]]:
                for condition in assertion[keys[0]][obj]:
                    result = result & (state.resources[obj][condition] == assertion[keys[0]][obj][condition])
        if keys[1] in assertion:
            for obj in assertion[keys[1]]:
                for condition in assertion[keys[0]][obj]:
                    result = result & (state.inventory[obj][condition] == assertion[keys[1]][obj][condition])
        return result

    # IDEA: Add learning once perceptual-dynamic-planner is setup

    #########################################################################
    # operators
    #########################################################################

    def move_forward(self, state):
        x,y,z = state.agent['cur_xyz']
        if (state.agent['cur_theta'] == DIR_NORTH):
            state.agent['cur_xyz'] = (x,y,z-1)
        if (state.agent['cur_theta'] == DIR_EAST):
            state.agent['cur_xyz'] = (x+1,y,z)
        if (state.agent['cur_theta'] == DIR_SOUTH):
            state.agent['cur_xyz'] = (x,y,z+1)
        if (state.agent['cur_theta'] == DIR_WEST):
            state.agent['cur_xyz'] = (x-1,y,z)
        return state

    def turn_left(self, state):
        state.agent['cur_theta'] = look_left_deltas[state.agent['cur_theta']]
        return state

    def turn_right(self, state):
        state.agent['cur_theta'] = look_right_deltas[state.agent['cur_theta']]
        return state

    def break_block(self, state, target):
        state.resources[target]['state'] = -1
        return state

    def search(self, target):
        target_id = self.object_id[target]
        for coords in self.visual_percept['coords']:
            if self.visual_percept['blocks'][coords] == target_id:
                self.state.resources[target]['location'] = coords
                return state
        return False

    #########################################################################
    # methods
    #########################################################################

    # TODO: change methods to suit new variable + knowledge structure
    # main task method. currently only way to get the resource
    def get_resource(self, state):
        print("calling get_resource")
        #multiple "check-points" to plan to and then replan/plan for the later part
        if self.check_assertion(self.assertions[1], state) == 1:
            return [('move_closer',)]
        if self.check_assertion(self.assertions[2], state) == 1:
            return [('acquire_gold')]
        return [('search_for_gold',)]

    def search_for_gold(self, state):
        # TODO: new logic for 360 deg rounds until gold is sighted
        if self.state.turn_start == None:
            self.state.turn_start = self.state.agent['cur_theta']
        elif self.state.turn_start == self.state.agent['cur_theta']:
            return False
        return [('turn_right',),('search','gold')]
        # if the current percept has gold --> continue to navigation
        # if not --> move and get percept again

    def move_closer(self, state):
        return state
        # TODO: new logic for navigation as per visual percept
        # print("calling navigate with target: {}".format(target))
        # if state.path_idx == len(state.path):
        #     print("setting "+target+" to reached")
        #     state.targets[target]['reached'] = 1
        #     return []
        # if state.path_found == 1 and state.targets[target]['reached'] == 0:
        #     cur_x,cur_y,cur_z = state.agent['cur_xyz']
        #     next_x,next_y,next_z = state.path[state.path_idx]
        #     if next_x > cur_x:
        #         if state.agent['cur_theta'] == DIR_EAST:
        #             state.path_idx = state.path_idx + 1
        #             return [('move_forward',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_WEST:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_NORTH:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_SOUTH:
        #             return [('turn_left',), ('navigate', target)]
        #     elif next_x < cur_x:
        #         if state.agent['cur_theta'] == DIR_WEST:
        #             state.path_idx = state.path_idx + 1
        #             return [('move_forward',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_SOUTH:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_EAST:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_NORTH:
        #             return [('turn_left',), ('navigate', target)]
        #     elif next_z > cur_z:
        #         if state.agent['cur_theta'] == DIR_SOUTH:
        #             state.path_idx = state.path_idx + 1
        #             return [('move_forward',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_EAST:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_NORTH:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_WEST:
        #             return [('turn_left',), ('navigate', target)]
        #     elif next_z < cur_z:
        #         if state.agent['cur_theta'] == DIR_NORTH:
        #             state.path_idx = state.path_idx + 1
        #             return [('move_forward',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_WEST:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_SOUTH:
        #             return [('turn_right',), ('navigate', target)]
        #         elif state.agent['cur_theta'] == DIR_EAST:
        #             return [('turn_left',), ('navigate', target)]
        #     return []
        # else:
        #     return False

    def acquire_resource(self, state, target):
        print("calling acquire with target: {}".format(target))
        if state.inventory[target] == 1:
            return []
        if state.resources[target]['state'] == 1:
            #gold block not yet broken
            #face the block, if already facing then break the block
            # TODO: probably agent will always face the block depending upon how navigation is implemented
            cur_x,cur_y,cur_z = state.agent['cur_xyz']
            next_x,next_y,next_z = state.targets[target]['location']
            if next_z < cur_z:
                if state.agent['cur_theta'] == DIR_NORTH:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_WEST:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_SOUTH:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_EAST:
                    return [('turn_left',), ('acquire_gold',target)]
            if next_z > cur_z:
                if state.agent['cur_theta'] == DIR_SOUTH:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_EAST:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_NORTH:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_WEST:
                    return [('turn_left',), ('acquire_gold',target)]
            if next_x < cur_x:
                if state.agent['cur_theta'] == DIR_WEST:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_EAST:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_SOUTH:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_NORTH:
                    return [('turn_left',), ('acquire_gold',target)]
            if next_x > cur_x:
                if state.agent['cur_theta'] == DIR_EAST:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_WEST:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_NORTH:
                    return [('turn_right',), ('acquire_gold',target)]
                elif state.agent['cur_theta'] == DIR_SOUTH:
                    return [('turn_left',), ('acquire_gold',target)]
            return []
        else:
            # gold block is broken, but not yet acquired
            state.targets[target]['acquired'] = 1
            return [('move_forward',), ('acquire_gold', target)]
