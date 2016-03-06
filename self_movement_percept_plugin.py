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
FREQUENCY = 1

# probably make this a subclass of some generic agent state
class AgentMovementState:
    def __init__(self, pos=None, facing=None, moving=None, turning=None):
        # x, y, z integer only
        self.pos = Vector3(*pos) if pos else None
        # cardinal directions only
        self.dir = facing
        # if the agent is moving or turning
        self.moving = moving
        self.turning = turning


@pl_announce('SelfMovementPercept')
class SelfMovementPerceptPlugin(PluginBase):

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
        self.state = AgentMovementState()
        # actual position/direction used to compute moving/turning
        self.absolute_pos = None
        self.absolute_dir = None

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
        self.event.emit('agent_position_state')


    def handle_client_join(self, name, data):
        logger.info("Initializing agent's internal movement state")
        self.handle_update_sensors()


    def handle_update_sensors(self):
        pos = self.clientinfo.position
        self.state.facing = mvu.get_nearest_direction(pos.yaw)
        x,y,z = mvu.get_nearest_position(pos.x, pos.y, pos.z)
        self.state.pos = Vector3(x,y,z)

        self.state.turning = self.is_turning()
        self.state.moving = self.is_moving()

        mvu.log_agent_state(self.state)


    def handle_position_reset(self, name, data):
        pass


    def handle_path_done(self, name, data):
        pass


    #########################################################################
    # Helper unctions for updating internal agent state
    #########################################################################

    def is_turning(self):
        if self.absolute_dir is None:
            return False

        diff = abs(self.absolute_dir - self.clientinfo.position.yaw)
        if diff > EPSILON_DIR:
            return True
        return False


    def is_moving(self):
        if self.absolute_pos is None:
            return False

        dist = math.sqrt(
            (self.absolute_pos.x - self.clientinfo.position.x)**2 +
            (self.absolute_pos.y - self.clientinfo.position.y)**2 +
            (self.absolute_pos.z - self.clientinfo.position.z)**2)
        if dist > EPSILON_DIST:
            return True
        return False
