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
FREQUENCY = 0.5

# probably make this a subclass of some generic agent state
class AgentMovementPrimitive:
    def __init__(self, pos=None, facing=None, moving=None, turning=None):
        # forward or none. faster movement occurs at higher freq
        self.delta_pos = pos if pos else 'NONE'
        # left ro right
        self.delta_dir = facing if facing else 'NONE'
        # if the agent is moving or turning
        # self.moving = moving
        # self.turning = turning


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

        # the agent's records of its own motion. updates every x seconds
        # will be an integer block position, with the agent at the center
        self.motion = AgentMovementPrimitive()
        # previous position/direction in world-relative values
        # used for computing motion internally. **not recorded by agent**
        # changes according to motion primitives
        self.state = None
        # timer to update the agent's knowledge of its own movement
        frequency = FREQUENCY
        self.timers.reg_event_timer(frequency, self.sensor_timer_tick)


    #########################################################################
    # Timers and event handlers
    #########################################################################

    # not a normal event handler. simply triggered every x seconds
    def sensor_timer_tick(self):
        self.handle_update_sensors()

        # TODO: This has to be called with some data. e.g. formatted state
        self.event.emit('agent_movement_primitive_percept')


    def handle_client_join(self, name, data):
        logger.info("Initializing agent's internal movement state")
        self.handle_update_sensors()


    def handle_update_sensors(self):
        pos = self.clientinfo.position

        # update absolute state as well as current movement primitive
        delta_pos = mvu.get_nearest_delta_pos(self.state.pos, Vector3(pos.x, pos.y, pos.z))
        self.motion.delta_pos = motion_labels[delta_pos]
        delta_dir = mvu.get_nearest_delta_dir(self.state.dir, pos.yaw)
        self.motion.delta_dir = motion_labels[delta_dir]
        # update absolute state only if necessary
        if delta_pos != MOVE_NONE:
            x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
            self.state.pos = Vector3(x, y, z)
        if delta_dir != TURN_NONE:
            facing = mvu.get_nearest_direction(pos.yaw)
            self.state.dir = facing

        mvu.log_agent_motion(self.motion)


    def handle_position_reset(self, name, data):
        pass


    def handle_path_done(self, name, data):
        pass
