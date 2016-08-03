import logging
import time
import copy

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from pyhop import hop, helpers

from test_room_plugin import TestRoomPlugin, START_COORDS
import utils.movement_utils as mvu
from utils.constants import *

ACTION_TICK_FREQUENCY = 1.5

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
        'execute_plan'      : 'register_execution_timer',
        'execution_success' : 'call_continual_planner',
        'action_completed'  : 'update_perception',
        'assertion_true'    : 'call_continual_planner',
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
            self.exec_state.agent['start_xyz'] = mvu.get_nearest_position(pos.x, pos.y, pos.z)
            self.exec_state.agent['cur_xyz'] = self.exec_state.agent['start_xyz']
            self.exec_state.agent['start_theta'] = mvu.get_nearest_direction(pos.yaw)
            self.exec_state.agent['cur_theta'] = self.exec_state.agent['start_theta']
            self.state = copy.deepcopy(self.exec_state)
            helpers.rename_state(self.state, 'simulation_start_state')
            block_pos = data['location']
            self.perceive()
            # for block in self.visual_percept['blocks']:
            #     print(type(block))
            #     print(type(self.visual_percept['blocks'][block]))
                #  print([block," ",self.visual_percept['blocks'][block]])
            # self.state.targets['gold']['location'] = (
            #     block_pos['x'],
            #     block_pos['y'],
            #     block_pos['z'])
            self.continual_planner()


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
        logger.info("triggered execution")
        self.timers.reg_event_timer(ACTION_TICK_FREQUENCY, self.executor, 1)

    def call_continual_planner(self, name, data):
        logger.info("need to (re)plan")
        self.continual_planner()

    def update_perception(self, name, data):
        logger.info("updating state with perception")
        self.monitor()

    def init_operators(self):
        self.op_translations = {
            'move_forward'          : self.atomicoperators.operator_move,
            'turn_left'             : self.atomicoperators.operator_look_left,
            'turn_right'            : self.atomicoperators.operator_look_right,
            'break_block'           : self.atomicoperators.operator_break_obstacle,
            'search_placeholder'    : self.search,
        }

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
            self.break_block,
            self.search_placeholder,)
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
        self.exec_state = hop.State('execution_start_state')
        # TODO: convert everything into one directory which has 'resource', 'inventory' key all in one
        # variables in this minecraft world
        self.PLAN_STATUS = None
        # 0: Rendered obsolete by assertions, 1: All okay, 2: Error, need replanning or introspection, 9001: Success
        self.ASSERT_ID = None
        # id of the assertion held true right now
        self.ERROR_ID = None
        self.METHOD_ID = None
        self.error = {}
        self.error = {
            1: None,
        }
        self.exec_state.target = 'gold'
        self.plan_idx = 0
        self.exec_state.turn_num = 0
        self.exec_state.objects = {
            'gold',
            'stone_block',
        }
        self.exec_state.object_id = {
            'gold'          : 41,
            'stone_block'   : 100
        }
        self.exec_state.tools = {}
        # information structure for keeping track of world state
        self.exec_state.resources = {}
        for obj in self.exec_state.objects:
            self.exec_state.resources[obj] = {
                'state':        None,
                'hemisphere':   None,
                'location':     None,
            }
        # information structure to keep track of self state
        # State = None: not located yet, 0: seen but not near, 1: near, -1: broken/acquired
        # Hemisphere = None: Haven't seen so far, -1: was to the left of the cone,
        # 0: was in the center, +1: was to the right of the cone
        self.exec_state.agent = {
            'cur_xyz':       None,
            'cur_theta':    None,
            'start_xyz':     None,
            'start_theta':  None,
        }
        self.exec_state.inventory = {}
        for obj in self.exec_state.objects:
            self.exec_state.inventory[obj] = 0
        # self.state.need_percept = 0
        # set state variables to be used by operators and methods
        self.state = hop.State('simulation_start_state')
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
                'method_id': 0,
            },
            # gold must be in sight to plan how to navigate
            2: {
                'resources': {
                    'gold': {
                        'state': 1,
                    },
                },
                'inventory': {
                    'gold': 0
                },
                'method_id': 1,
            },
            3: {
                'inventory': {
                    'gold': 1,
                },
                'method_id': 2
            },
            # agent must be next to gold block to plan how to break it
        }

    #########################################################################
    # planner and real-time execution helper functions
    #########################################################################

    def continual_planner(self):
        # a function which executes returned plan, senses
        # percepts and decides if replanning should be done
        # get initial plan
        # self.state = copy.deepcopy(self.exec_state)
        # helpers.rename_state(self.state, 'simulation_start_state')
        self.solve()
        if self.room_plan is not None and len(self.room_plan) > 0:
            self.PLAN_STATUS = 1
            self.plan_idx = 0
            logger.info("agent planning completed")
            logger.info("total room plan: {}".format(self.room_plan))
            self.event.emit("execute_plan")
        elif self.PLAN_STATUS == 9001:
            logger.info("Plan: Success")
        elif self.PLAN_STATUS == 2:
            logger.info("Could not find a plan. Planner exited with STATUS: 2")
            self.event.emit("agent_planning_failed")
            if self.ERROR_ID == 1:
                logger.info("Failed method: {}".format(self.error[1]))
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

    def executor(self):
        logger.info("In agent executor")
        # will basically just execute action represented at self.plan_idx index in the plan
        plan_op = self.room_plan[self.plan_idx]
        if len(plan_op)>1:
            logger.info("Detected tuple of function and arguments")
            self.op_translations[plan_op[0]](plan_op[1:])
        else:
            self.op_translations[plan_op[0]]()
        self.event.emit("action_completed")
        self.plan_idx += 1
        if self.plan_idx == len(self.room_plan):
            logger.info("complete plan executed")
            self.room_plan = []
            self.event.emit("execution_success")
            return
        return

    def monitor(self):
        # MONITORS by refreshing perception --> monitoring surroundings
        # MONITORS by monitoring assertions and plan execution
        # TODO: assertion_monitor should be a part of perception, and should be evaluated after every action + perception cycle, if no assertions are true --> call executor again
        self.perceive()
        self.update_state(self.exec_state)
        self.update_state(self.state)
        self.assertion_monitor(self.exec_state)
        if self.ASSERT_ID == None:
            self.event.emit("execute_plan")
        else:
            logger.info("assertion check came true. Assertion #{}".format(self.ASSERT_ID))
            self.event.emit("assertion_true")
        return

    def assertion_monitor(self, state):
        # monitor --> replan if assertion is fulfilled
        # later --> compare and analyze expected VS actual state
        # TODO: state dependency of assertions
        for assertion in self.assertions:
            result = self.check_assertion(self.assertions[assertion], state)
            if result == True:
                self.PLAN_STATUS = 0
                self.ASSERT_ID = assertion
                return
        self.ASSERT_ID = None
        return

    def check_assertion(self, assertion, state):
        # directories where assertions could be checked
        keys = ['resources', 'inventory', 'method_id']
        result = True
        if keys[0] in assertion:
            for obj in assertion[keys[0]]:
                for condition in assertion[keys[0]][obj]:
                    if isinstance(assertion[keys[0]][obj][condition], list):
                        temp_result = False
                        for condition_n in assertion[keys[0]][obj][condition]:
                            temp_result = temp_result | (state.resources[obj][condition] == condition_n)
                        result = result & temp_result
                    else:
                        result = result & (state.resources[obj][condition] == assertion[keys[0]][obj][condition])
        if keys[1] in assertion:
            for obj in assertion[keys[1]]:
                result = result & (state.inventory[obj] == assertion[keys[1]][obj])
        if keys[2] in assertion:
            result = result & (self.METHOD_ID == assertion[keys[2]])
        return result

    def update_state(self, state):
        if self.visual_percept['blocks'][(0,1)] == state.object_id[state.target]:
            logger.info("near the gold block!")
            state.resources[state.target]['state'] = 1
        if state.resources[state.target]['state'] == 1 and self.visual_percept['blocks'][(0,1)] == 0:
            state.resources[state.target]['state'] = -1
            state.inventory[state.target] = 1

    def search(self, arguments):
        logger.info("calling search action")
        target = arguments[0]
        target_id = self.exec_state.object_id[target]
        for coords in self.visual_percept['coords']:
            if self.visual_percept['blocks'][coords] == target_id:
                logger.info("found the gold block")
                self.exec_state.resources[target]['location'] = coords
                self.exec_state.resources[target]['state'] = 0
                self.state.resources[target]['location'] = coords
                self.state.resources[target]['state'] = 0
                self.PLAN_STATUS = 0
                return
        logger.info("couldn't find the gold block")
        self.PLAN_STATUS = 2
        return

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

    def break_block(self, state):
        state.resources[state.target]['state'] = -1
        state.inventory[state.target]= 1
        return state

    def search_placeholder(self, state, target):
        # just a PyHop placeholder for actual function
        return state

    #########################################################################
    # methods
    #########################################################################

    # TODO: change methods to suit new variable + knowledge structure
    # main task method. currently only way to get the resource
    def get_resource(self, state):
        print("calling get_resource")
        #multiple "check-points" to plan to and then replan/plan for the later part
        if self.ASSERT_ID == 1:
            self.METHOD_ID = 1
            logger.info("Planning to move closer")
            return [('move_closer','gold',)]
        if self.ASSERT_ID == 2:
            self.METHOD_ID = 2
            logger.info("Planning to acquire gold")
            return [('acquire_gold','gold')]
        if self.ASSERT_ID == 3:
            self.METHOD_ID = 3
            logger.info("SUCCESSFULLY ACQUIRED GOLD")
            return []
        self.METHOD_ID = 0
        logger.info("Planning to search for gold")
        return [('search_for_gold',)]

    def search_for_gold(self, state):
        # TODO: new logic for 360 deg rounds until gold is sighted
        if self.state.turn_num == 0:
            self.state.turn_num = self.state.turn_num + 1
            return [('search_placeholder', 'gold')]
        elif self.state.turn_num == 4:
            self.PLAN_STATUS = 2
            self.error_id = 1
            self.error[self.ERROR_ID] = 'search_for_gold'
            logger.info("Unsuccessful 360 deg search for gold.")
            return False
        self.state.turn_num = self.state.turn_num + 1
        return [('turn_right',),('search_placeholder','gold')]
        # if the current percept has gold --> continue to navigation
        # if not --> move and get percept again

    def move_closer(self, state, target):
        logger.info("in method: move_closer")
        forward_moves = state.resources[target]['location'][1]
        side_moves = state.resources[target]['location'][0]
        temp_plan = []
        if side_moves != 0:
            for i in range(forward_moves):
                temp_plan.append(('move_forward',))
        else:
            for i in range(forward_moves-1):
                temp_plan.append(('move_forward',))
        if side_moves>0:
            temp_plan.append(('turn_right',))
        elif side_moves<0:
            temp_plan.append(('turn_left',))
        for i in range(abs(side_moves)-1):
            temp_plan.append(('move_forward',))
        state.resources[target]['state'] = 1
        return temp_plan

    def acquire_resource(self, state, target):
        print("calling acquire with target: {}".format(target))
        if state.resources[target]['state'] == 1:
            return [('break_block',),]
