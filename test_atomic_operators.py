import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

#from utils.constants import *
#import utils.movement_utils as mvu

FREQUENCY = 3

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')


def mseq = []
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
        self.timers.reg_event_timer(frequency, self.move_sequence_tick)
        self.seq_index = 0


    def move_sequence_tick(self):
        if mseq[self.seq_index] == "move":
            self.atomicoperators.operator_move()
        elif mseq[self.seq_index] == "turn_left":
            self.atomicoperators.operator_turn_left()
        elif mseq[self.seq_index] == "turn_right":
            self.atomicoperators.operator_turn_right()

        logger.info("agent executing command: {}".format(mseq[self.seq_index]))
        self.seq_index = (self.seq_index+1)%len(mseq)
