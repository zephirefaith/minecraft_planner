import logging

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

from utils.constants import *
import utils.movement_utils as mvu

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

# tick frequency for movement sensor
FREQUENCY = 0.4

# probably make this a subclass of some generic agent state
class AgentMovementPrimitive():
    def __init__(self, delta_pos=None, delta_dir=None):
        # movement is forward or none. faster movement is simply higher freq
        self.delta_pos = delta_pos if delta_pos else motion_labels[MOVE_NONE]
        # a turn is left, right or none
        self.delta_dir = delta_dir if delta_dir else motion_labels[TURN_NONE]

class AgentAbsoluteState:
    def __init__(self, abs_pos=None, abs_dir=None):
        # A Vector3 of (x,y,z) coordinates
        self.pos = abs_pos if abs_pos else None
        # compass direction in Minecraft yaw angle values
        self.dir = abs_dir if abs_dir else None

@pl_announce('SelfMovementSensor')
class SelfMovementSensorPlugin(PluginBase):

    requires = ('Event', 'Timers', 'ClientInfo',)

    events = {
        'movement_position_reset':  'handle_position_reset',
        'movement_path_done':       'handle_path_done',
        'client_join_game':         'handle_client_join',
    }

    def __init__(self, ploader, settings):
        super(SelfMovementSensorPlugin, self).__init__(ploader, settings)
        # agent's records of its own motion
        # egocentric (not grounded in any world knowledge)
        self.motion = AgentMovementPrimitive()
        # previous absolute position/direction the world
        # used for computing motion internally. *not recorded by agent*
        self.state = AgentAbsoluteState()
        # timer to update the agent's knowledge of its own movement
        frequency = FREQUENCY
        self.timers.reg_event_timer(frequency, self.sensor_timer_tick)

    #########################################################################
    # Timers and event handlers
    #########################################################################

    # not a normal event handler. simply triggered every x seconds
    def sensor_timer_tick(self):
        self.handle_update_sensors()
        data = {
            'delta_pos': self.motion.delta_pos,
            'delta_dir': self.motion.delta_dir,
        }
        # percept: small amount of processing to determine last action
        self.event.emit('agent_action_percept', data)

    def handle_client_join(self, name, data):
        pos = self.clientinfo.position
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        self.state.pos = Vector3(x, y, z)
        facing = mvu.get_nearest_direction(pos.yaw)
        self.state.dir = facing
        logger.info("Initializing agent's internal state of motion")

    def handle_update_sensors(self):
        pos = self.clientinfo.position
        # discretize the absolute position and direction
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        cur_pos = Vector3(x, y, z)
        cur_dir = mvu.get_nearest_direction(pos.yaw)

        # update absolute state as well as current movement primitive
        delta_pos = mvu.get_nearest_delta_pos(self.state.pos, cur_pos)
        self.motion.delta_pos = motion_labels[delta_pos]
        delta_dir = mvu.get_nearest_delta_dir(self.state.dir, cur_dir)
        self.motion.delta_dir = motion_labels[delta_dir]
        #print("delta pos: {}, delta dir: {}".format(delta_pos, delta_dir))

        self.state.pos = cur_pos
        self.state.dir = cur_dir

        mvu.log_agent_motion(self.motion)
        mvu.log_agent_state(self.state)

    def handle_position_reset(self, name, data):
        pass

    def handle_path_done(self, name, data):
        pass
