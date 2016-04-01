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
            self.forward,
            self.turn_left,
            self.turn_right,
            self.break_block)
        hop.print_operators(hop.get_operators())

        # methods will be nested
        hop.declare_methods(
            'get_resource',
            self.find_route_to_resource,    # BFS() or A*
            self.navigate_to_resource,      # follow the path BFS spewed out
            self.acquire_resource)          # break the block and move forward
        hop.print_methods(hop.get_methods())

        # set state variables
        # will be used by operators and methods
        self.state = hop.State('start_state')
        self.state.start_loc = self.start_location
        self.state.current_loc = self.state.start_loc
        self.state.current_orientation = self.orientation
        self.state.goal_loc = self.gold_location
        self.state.block = 1                # 1: unbroken, 0: broken

        ploader.provides('TestAtomicOperators',self)

    #############
    # operators #
    #############

    # assuming location to be (x,y)
    def forward(self):
        if (self.state.current_orientation == 0):
            self.state.current_loc[1] = self.state.current_loc[1] + 1
        if (self.state.current_orientation == 1):
            self.state.current_loc[1] = self.state.current_loc[0] + 1
        if (self.state.current_orientation == 2):
            self.state.current_loc[1] = self.state.current_loc[1] - 1
        if (self.state.current_orientation == 3):
            self.state.current_loc[1] = self.state.current_loc[0] - 1

        return self.state

    def turn_left(self):
        self.state.current_orientation = self.state.current_orientation + 1
        return self.state

    def turn_right(self):
        self.state.current_orientation = self.state.current_orientation - 1
        return self.state

    def break_block(self):
        if(self.state.block == 1):
            self.state.block = 0
            return self.state
        return False

    ###########
    # methods #
    ###########

    def solution(self):
        # will be used to call the hop.plan command

    def find_route_to_resource(self):
        path = self.compute_path(self.state.current_loc, self.state.goal_loc)
        return path

    def

