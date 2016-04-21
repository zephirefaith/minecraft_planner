import logging

#from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
#from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

#from utils.constants import *
#import utils.movement_utils as mov
import utils.camera_utils as cam

__author__ = 'Bradley Sheneman'
logger = logging.getLogger('spockbot')

# tick frequency for both sensor types (visual, self-motion)
# allows sensors to run at different freq but still be coordinated
VISION_SENSOR_FREQUENCY = 1
MOTION_SENSOR_FREQUENCY = 0.6

@pl_announce('SensorTimers')
class SensorTimersPlugin(PluginBase):
    requires = ('Event', 'Timers', 'ClientInfo',)

    events = {
        'client_join_game': 'handle_client_join',
    }

    def __init__(self, ploader, settings):
        super(SensorTimersPlugin, self).__init__(ploader, settings)


    def motion_timer_tick(self):
        self.event.emit('sensor_tick_motion')


    def vision_timer_tick(self):
        pos = self.clientinfo.position
        data = {
            'x':pos.x,
            'y':pos.y,
            'z':pos.z,
            'pitch':pos.pitch,
            'yaw':pos.yaw,
        }
        self.event.emit('sensor_tick_vision', data)


    def handle_client_join(self, name, data):
        self.timers.reg_event_timer(VISION_SENSOR_FREQUENCY, self.vision_timer_tick)
        self.timers.reg_event_timer(MOTION_SENSOR_FREQUENCY, self.motion_timer_tick)
