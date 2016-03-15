import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from pyhop import hop

FREQUENCY = 3

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

mseq = [
    "move",
    "turn_left",
    "move",
    "move",
    "turn_right",
    "turn_right",
    "move",
    "move",
    "turn_right",
    "move",
    "turn_left",
    "turn_left",
]

@pl_announce('TestAtomicOperators')
class TestAtomicOperatorsPlugin(PluginBase):

    requires = ('Event', 'Timers', 'AtomicOperators')

    events = {
        #'movement_position_reset':  'handle_position_reset',
        #'movement_path_done':       'handle_path_done',
    }

    def __init__(self, ploader, settings):
        super(TestAtomicOperatorsPlugin, self).__init__(ploader, settings)
        frequency = FREQUENCY
        self.timers.reg_event_timer(frequency, self.sequence_tick)
        self.seq_index = 0

        logger.info("adding atomic operators to pyhop:")
        # note: can call declare_operators multiple times cor current situation
        hop.declare_operators(
            self.atomicoperators.operator_move,
            self.atomicoperators.operator_look_left,
            self.atomicoperators.operator_look_right)
        hop.print_operators(hop.get_operators())

        hop.declare_methods(
            'do_test_sequence',
            self.do_forward_sequence,
            self.do_reverse_sequence)
        hop.print_methods(hop.get_methods())

        # have to add fields like start_pos.did_forward_seq = False
        # and for the goal: goal_pos.did_forward_seq = True
        self.start_state = hop.State('start_state')
        self.goal_state1 = hop.Goal('goal_state1')
        self.goal_state2 = hop.Goal('goal_state2')

        ploader.provides('TestAtomicOperators',self)

    def sequence_tick(self):
        if mseq[self.seq_index] == "move":
            self.atomicoperators.operator_move()
        elif mseq[self.seq_index] == "turn_left":
            self.atomicoperators.operator_look_left()
        elif mseq[self.seq_index] == "turn_right":
            self.atomicoperators.operator_look_right()

        logger.info("\n******agent executing command: {}******\n".format(mseq[self.seq_index]))
        self.seq_index = (self.seq_index+1)%len(mseq)

    def do_forward_sequence(self, pos):
        if state.dist[x][y] <= 2:
            return [('walk',a,x,y)]
        return False

    def do_reverse_sequence(self, pos):
        if state.dist[x][y] <= 2:
            return [('walk',a,x,y)]
        return False
