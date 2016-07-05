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
#PERCEPT_REQUEST_FREQUENCY = 1

__author__ = ['Bradley Sheneman', 'Priyam Parashar']
logger = logging.getLogger('spockbot')

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
    # initializations
    #########################################################################

    def __init__(self, ploader, settings):
        super(VisualPlannerPlugin, self).__init__(ploader, settings)
        self.visual_percept = None
        self.init_planner()
        self.init_operators()
        ploader.provides('VisualPlanner', self)

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

    def init_operators(self):
        self.op_translations = {
            'move_forward': self.atomicoperators.operator_move,
            'turn_left': self.atomicoperators.operator_look_left,
            'turn_right': self.atomicoperators.operator_look_right,
            'break_block': self.atomicoperators.operator_break_obstacle,}

    def init_state(self):
        # set state variables to be used by operators and methods
        self.state = hop.State('start_state')
        self.state.gold = { 'state': None, 'hemisphere': None}
        # State = None: not located yet, 0: seen but not near, 1: near, -1: broken
        # Hemisphere = None: Haven't seen so far, -1: was to the left of the cone,
        # 0: was in the center, +1: was to the right of the cone
        self.state.resource = 0
        # 0: not acquired, 1: acquired
        self.state.need_percept = 0

        #goal state
        self.goal_state = hop.State('goal_state')
        self.state.gold = { 'state': -1, 'hemisphere': 0}
        self.goal_state.resource = 1
        #self.state.percept_update = 0
        #self.failed_method = None
        # self.preconditions = {
        #     'break_wall' : {
        #         'precondition'  : None,
        #         'inventory'     : ['iron'],
        #     },
        # }
        # self.methods = {
        #     'break_wall' : self.break_wall
        # }


    #########################################################################
    # plugin events
    #########################################################################

    def handle_client_join(self, name, data):
        pos = self.clientinfo.position
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        orientation = mvu.get_nearest_direction(pos.yaw)
        self.request_visual_percept(x, z, orientation)

    def handle_block_update(self, name, data):
        # gold block spawned in world. call the planner
        if data['block_data'] >> 4 == 41:
            pos = self.clientinfo.position
            self.state.start_loc = mvu.get_nearest_position(pos.x, pos.y, pos.z)
            self.state.current_position = self.state.start_loc
            self.state.current_orientation = mvu.get_nearest_direction(pos.yaw)

            block_pos = data['location']
            # self.state.targets['gold']['location'] = (
            #     block_pos['x'],
            #     block_pos['y'],
            #     block_pos['z'])

            self.solve()
            if self.room_plan is not None and len(self.room_plan) > 0:
                logger.info("plan succeeded")
                logger.info("total room plan: {}".format(self.room_plan))
                self.event.emit("agent_planning_complete")
                self.plan_idx = 0
            else:
                logger.info("plan failed")
                self.event.emit("agent_planning_failed")

    def handle_visual_percept(self, name, data):
        logger.debug("handling percept: {}".format(data))
        self.visual_percept = data

    def request_visual_percept(self, x, z, orientation):
        data = {
            'x':x,
            'y':13,
            'z':z,
            'pitch':0,
            'yaw':orientation,
        }
        logger.debug("sending request with data: {}".format(data))
        self.event.emit('sensor_tick_vision', data)

    def register_execution_timer(self, name, data):
        self.timers.reg_event_timer(ACTION_TICK_FREQUENCY, self.execute_and_monitor)

    def execute_and_monitor(self):
        # a function which executes returned plan, senses
        # percepts and decides if replanning should be done
        if not self.room_plan:
            print("no plan to execute")
            return
        plan_op = self.room_plan[self.plan_idx][0]
        self.op_translations[plan_op]()
        self.plan_idx += 1
        if self.plan_idx == len(self.room_plan):
            self.room_plan = []
            self.init_state()
        return False

    # def percept_request_tick(self):
    #     pos = self.clientinfo.position
    #     x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
    #     orientation = mvu.get_nearest_direction(pos.yaw)
    #     self.request_visual_percept(x, z, orientation)
    #########################################################################
    # planner helper functions
    #########################################################################

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
        print("last failed method label: {}".format(self.failed_method))
        # if self.failed_method:
        #     self.learning_state = copy.deepcopy(self.state)
        #     self.learning_state.targets['wall']['reached'] = 1
        #     result = self.improvise(self.learning_state, self.failed_method, self.error_type)
        #     if result == True:
        #         print("Learnt a new object just fine!")
        #         self.room_plan = hop.plan(self.state,
        #                             [('get_resource',)],
        #                             hop.get_operators(),
        #                             hop.get_methods(),
        #                             verbose=3)
        #     else:
        #         print("Could not learn anything :(")

    def execution_tick(self):
    #executor which executes, senses and replans --> maybe call a different agent_executor here?
        if not self.room_plan:
            print("no plan to execute")
            return
        plan_op = self.room_plan[self.plan_idx][0]
        self.op_translations[plan_op]()
        self.plan_idx += 1
        if self.plan_idx == len(self.room_plan):
            self.room_plan = []
            self.init_state()

    # TODO: Add learning once perceptual-dynamic-planner is setup

    # a function for learning a new method or a new tool
    # def improvise(self, sim_state, method_name, error_type):
    #     # see what kind of error it is, if it's a precondition error, learn a
    #     # new method for these preconditions.
    #     # if it is an inventory error and then try the current inventory and
    #     # see if an inventory edit can be learnt
    #     if error_type == 'inventory':
    #         #call the same function but with current available inventory
    #         for tool in self.state.inventory:
    #             if self.state.inventory[tool] == 1:
    #                 tool_list = []
    #                 tool_list.append(tool)
    #                 result = hop.plan(sim_state,
    #                             [(method_name, tool_list)],
    #                             hop.get_operators(),
    #                             hop.get_methods(),
    #                             verbose=2) #[method_name](sim_state, [tool])
    #                 if result is not None:
    #                     self.preconditions['break_wall']['inventory'].append(tool)
    #                     return True
    #         return False
    #     else:
    #         print("NOT IMPLEMENTED YET! NEEDS REINFORCEMENT LEARNING MODULE TO LEARN A NEW METHOD!")


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
        return state

    def turn_left(self, state):
        state.current_orientation = look_left_deltas[state.current_orientation]
        return state

    def turn_right(self, state):
        state.current_orientation = look_right_deltas[state.current_orientation]
        return state

    def break_block(self, state, target):
        if state.equipment == 'steel' or state.equipment == 'iron':
            state.targets[target]['broken'] = 1
            return state
        else:
            return False

    # def equip_agent(self, state, tool):
    #     if tool is None:
    #         return False
    #     else:
    #         state.equipment = tool
    #         return state

    #########################################################################
    # methods
    #########################################################################
    # main task method. currently only way to get the resource
    def get_resource(self, state):
        print("calling get_resource")
        #multiple "check-points" to plan to and then replan/plan for the later part
        if self.state.gold['state'] = None:
            return [('search_for_gold',)]
        if self.state.gold['state'] = 0:
            return [('move_closer',)]
        if self.state.gold['state'] = 1:
            return [('acquire_gold')]
        return [('search_for_gold',),('move_closer',),('acquire_gold',)]

    def search_for_gold(self, state):
        print("getting sensor data")
        pos = self.clientinfo.position
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        orientation = mvu.get_nearest_direction(pos.yaw)
        self.request_visual_percept(x, z, orientation)
        print(self.visual_percept)
        i=0
        for coords in self.visual_percept['coords']:
            i=i+1
            if i == 1:
                continue
            else:
                if self.visual_percept['blocks'][coords] == 35:
                    self.state.gold_in_sight = 1
                    break
        if self.state.gold_in_sight == 0:
            self.state.need_percept = 1
            print("Turning 360 deg clockwise to locate gold")
            return ['turn_right']
        else:
            print("gold found")
            return []
        # if the current percept has gold --> continue to navigation
        # if not --> move and get percept again

    def move_closer(self, state):
        print("calling navigate with target: {}".format(target))
        if state.path_idx == len(state.path):
            print("setting "+target+" to reached")
            state.targets[target]['reached'] = 1
            return []
        if state.path_found == 1 and state.targets[target]['reached'] == 0:
            cur_x,cur_y,cur_z = state.current_position
            next_x,next_y,next_z = state.path[state.path_idx]
            if next_x > cur_x:
                if state.current_orientation == DIR_EAST:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate', target)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_left',), ('navigate', target)]
            elif next_x < cur_x:
                if state.current_orientation == DIR_WEST:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate', target)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_left',), ('navigate', target)]
            elif next_z > cur_z:
                if state.current_orientation == DIR_SOUTH:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate', target)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_left',), ('navigate', target)]
            elif next_z < cur_z:
                if state.current_orientation == DIR_NORTH:
                    state.path_idx = state.path_idx + 1
                    return [('move_forward',), ('navigate', target)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('navigate', target)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_left',), ('navigate', target)]
            return []
        else:
            return False

    def acquire_resource(self, state, target):
        print("calling acquire with target: {}".format(target))
        if state.targets[target]['acquired'] == 1:
            return []
        if (state.targets[target]['reached'] == 1 and
            state.targets[target]['broken'] == 0):
            #gold block not yet broken
            #face the block, if already facing then break the block
            cur_x,cur_y,cur_z = state.current_position
            next_x,next_y,next_z = state.targets[target]['location']
            if next_z < cur_z:
                if state.current_orientation == DIR_NORTH:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire',target)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_left',), ('acquire',target)]
            if next_z > cur_z:
                if state.current_orientation == DIR_SOUTH:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire',target)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_left',), ('acquire',target)]
            if next_x < cur_x:
                if state.current_orientation == DIR_WEST:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire',target)]
                elif state.current_orientation == DIR_EAST:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_left',), ('acquire',target)]
            if next_x > cur_x:
                if state.current_orientation == DIR_EAST:
                    state.targets[target]['broken'] = 1
                    return [('break_block',target), ('acquire',target)]
                elif state.current_orientation == DIR_WEST:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_NORTH:
                    return [('turn_right',), ('acquire',target)]
                elif state.current_orientation == DIR_SOUTH:
                    return [('turn_left',), ('acquire',target)]
            return []
        else:
            # gold block is broken, but not yet acquired
            state.targets[target]['acquired'] = 1
            return [('move_forward',), ('acquire', target)]

    def break_wall(self, state, tools):
        # tools = preconditions['break_wall']['inventory']
        # check preconditions:
        tool = None
        for sample_tool in tools:
            print("checking if %s is available", sample_tool)
            if self.state.inventory[sample_tool] == 1:
                tool = sample_tool

        if tool is None:
            self.failed_method = 'break_wall'
            self.error_type = 'inventory'
            return False
        # if wall hasn't been reached at this point, method fails
        if state.targets['wall']['reached'] == 0:
            print("wall has not been reached yet")
            self.failed_method = 'break_wall'
            self.error_type = 'preconditions'
            return False
        # actual method execution
        if state.equipment is None:
            print("adding method equip_agent")
            return [('equip_agent', tool),('break_wall', tools)]
        elif state.targets['wall']['broken'] == 0:
            print("adding method break_block on wall")
            return [('acquire','wall')]
        return False
