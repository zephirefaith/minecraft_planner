import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from pyhop import hop

from test_room_plugin import TestRoom

__author__ = 'Priyam Parashar'
logger = logging.getLogger('spockbot')

@pl_announce('TestPlanner')
class TestPlannerPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo', 'World', 'TestRoom')

    events = {
        #'movement_position_reset':  'handle_position_reset',
        #'movement_path_done':       'handle_path_done',
    }

    orientation = {'N', 'E', 'S', 'W'}

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

        # methods will be nested
        hop.declare_methods(
            'get_resource',
            self.find_route_to_resource,    # BFS() or A*
            self.navigate_to_resource,      # follow the path BFS spewed out
            self.acquire_resource)          # break the block and move move_forward
        hop.print_methods(hop.get_methods())

        # set state variables
        # will be used by operators and methods
        self.state = hop.State('start_state')
        self.state.start_loc = self.start_location
        self.state.current_position = self.state.start_loc
        self.state.current_orientation = self.orientation
        self.state.goal_loc = self.gold_location
        self.state.gold = 1                # 1: unbroken, 0: broken
        self.state.path = []
        self.state.gold_reached = 0
        self.state.path_found = 0
        self.state.path_idx = -1
        self.state.gold_acquired = 0

        ploader.provides('TestPlanner',self)

    #############
    # operators #
    #############

    # assuming location to be (x,y)
    def move_forward(self):
        if (self.state.current_orientation == 0):
            self.state.current_position[1] = self.state.current_position[1] + 1
        if (self.state.current_orientation == 1):
            self.state.current_position[1] = self.state.current_position[0] + 1
        if (self.state.current_orientation == 2):
            self.state.current_position[1] = self.state.current_position[1] - 1
        if (self.state.current_orientation == 3):
            self.state.current_position[1] = self.state.current_position[0] - 1

        return self.state

    def turn_left(self):
        self.state.current_orientation = self.state.current_orientation + 1
        return self.state

    def turn_right(self):
        self.state.current_orientation = self.state.current_orientation - 1
        return self.state

    def break_block(self):
        if(self.state.gold == 1):
            self.state.gold = 0
            return self.state
        return False

    ###########
    # methods #
    ###########

    def solution(self):
        self.room_plan = hop.plan(self.state,
                            [('get_resource')],
                            hop.get_operators(),
                            hop.get_methods())
        if not self.room_plan:
            return False
        else:
            return True

    def find_route_to_resource(self):
        if not self.state.path:
            self.state.path = self.testroom.compute_path(self.state.current_position, self.state.goal_loc)
            if not self.state.path:
                return False
            else:
                self.state.path_found = 1
                self.state.path_length = len(self.state.path)
                self.state.path_idx = 0
        return None

    def navigate_to_resource(self):
        if self.state.path_found == 1 and self.state.gold_reached == 0:
            next_position = self.state.path[self.state.path_idx]
            if self.state.path_idx == (len(self.state.path) - 1):
                self.state.gold_reached == 1
                return False
            if next_position[0]>self.state.current_position[0]:
                if self.state.current_orientation == 1:
                    self.state.path_idx = self.state.path_idx + 1
                    return [('move_forward')]
                elif self.state.current_orientation == 3:
                    return [('turn_right')]
                elif self.state.current_orientation == 0:
                    return [('turn_right')]
                elif self.state.current_orientation == 2:
                    return [('turn_left')]
            if next_position[0]<self.state.current_position[0]:
                if self.state.current_orientation == 3:
                    self.state.path_idx = self.state.path_idx + 1
                    return [('move_forward')]
                elif self.state.current_orientation == 2:
                    return [('turn_right')]
                elif self.state.current_orientation == 1:
                    return [('turn_right')]
                elif self.state.current_orientation == 0:
                    return [('turn_left')]
            if next_position[1]>self.state.current_position[1]:
                if self.state.current_orientation == 0:
                    self.state.path_idx = self.state.path_idx + 1
                    return [('move_forward')]
                elif self.state.current_orientation == 3:
                    return [('turn_right')]
                elif self.state.current_orientation == 2:
                    return [('turn_right')]
                elif self.state.current_orientation == 1:
                    return [('turn_left')]
            if next_position[1]<self.state.current_position[1]:
                if self.state.current_orientation == 2:
                    self.state.path_idx = self.state.path_idx + 1
                    return [('move_forward')]
                elif self.state.current_orientation == 1:
                    return [('turn_right')]
                elif self.state.current_orientation == 0:
                    return [('turn_right')]
                elif self.state.current_orientation == 3:
                    return [('turn_left')]
        else:
            return False

    def acquire_resource(self):
        if self.state.gold_reached == 1 and self.state.gold_acquired == 0:
            if self.state.gold == 1:
                #gold block is unbroken
                #face the block, if already facing then break the block
                if self.state.goal_loc[1]<self.state.current_position[1]:
                    if self.state.current_orientation == 2:
                        return [('break_block')]
                    elif self.state.current_orientation == 1:
                        return [('turn_right')]
                    elif self.state.current_orientation == 0:
                        return [('turn_right')]
                    elif self.state.current_orientation == 3:
                        return [('turn_left')]
                if self.state.goal_loc[1]>self.state.current_position[1]:
                    if self.state.current_orientation == 0:
                        return [('break_block')]
                    elif self.state.current_orientation == 3:
                        return [('turn_right')]
                    elif self.state.current_orientation == 2:
                        return [('turn_right')]
                    elif self.state.current_orientation == 1:
                        return [('turn_left')]
                if self.state.goal_loc[0]<self.state.current_position[0]:
                    if self.state.current_orientation == 3:
                        return [('break_block')]
                    elif self.state.current_orientation == 1:
                        return [('turn_right')]
                    elif self.state.current_orientation == 2:
                        return [('turn_right')]
                    elif self.state.current_orientation == 0:
                        return [('turn_left')]
                if self.state.goal_loc[0]>self.state.current_position[0]:
                    if self.state.current_orientation == 1:
                        return [('break_block')]
                    elif self.state.current_orientation == 3:
                        return [('turn_right')]
                    elif self.state.current_orientation == 0:
                        return [('turn_right')]
                    elif self.state.current_orientation == 2:
                        return [('turn_left')]

            else:
                self.state.gold_acquired = 1
                return [('move_forward')]
        else:
            return False



