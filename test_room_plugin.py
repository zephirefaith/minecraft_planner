"""
An basic puzzle room. Creates the room, sets a start location and range

useful methods from Dimension (extended by World plugin):
    get_block() # get the block at a location
    get_block_entity_data() # get entity info at a location
    get_light() # get light level at location
    get_biome() # get biome at location
"""

import logging
import math
import collections as coll

from spockbot.mcdata import blocks
from spockbot.plugins.base import PluginBase, pl_announce
from spockbot.plugins.tools.event import EVENT_UNREGISTER
from spockbot.vector import Vector3

__author__ = 'Bradley Sheneman'

logger = logging.getLogger('spockbot')


# room coordinates (found in test_room_island)
MIN_X = -70
MIN_Y = 13
MIN_Z = -54

MAX_X = -62
MAX_Y = 15
MAX_Z = -38

START_COORDS = (-66,13,-39)

# have to create a dummy class like this
# in order to use your custom plugin in other plugins as a 'requires'
class TestRoomCore(object):
    def __init__(self, world, dims):
        self.world = world
        self.dims = dims

    def is_reachable(self, pos0, pos1):
        path = self.compute_path(pos0, pos1, max_depth=5)
        if path:
            #print("the path: "path)
            return True
        return False

    # note is_obstacle and is_gap ONLY WORK WITH BASIC BLOCKS
    # e.g. any block that is not air is considered an obstacle/walkable floor

    # checks the block above the given floor location to see if it is passable
    def is_obstacle(self, x, y, z):
        block = self.world.get_block(x, y+1, z)
        print(block)
        if block[0] != 0:
            return True
        return False

    # checks the given floor location to see if it is a gap
    def is_gap(self, x, y, z):
        block = self.world.get_block(x, y, z)
        print(block)
        if block[0] == 0:
            return True
        return False

    def is_traversable(self, pos):
        x,y,z = pos
        if self.is_obstacle(x, y, z) or self.is_gap(x, y, z):
            print("block is not traversable")
            return False
        return True


    def compute_path(self, pos0, pos1, max_depth):
        grnd = self.dims['min_y']
        minx = self.dims['min_x']
        maxx = self.dims['max_x']
        minz = self.dims['min_z']
        maxz = self.dims['max_z']

        start_pos = (math.floor(pos0[0]),math.floor(pos0[1]),math.floor(pos0[2]))
        end_pos = (math.floor(pos1[0]),math.floor(pos1[1]),math.floor(pos1[2]))
        search_queue = coll.deque()

        best_dist ={(x,pos0[1],z):float("inf")
            for x in range(minx,maxx+1)
            for z in range(minz,maxz+1)}
        best_dist[start_pos] = 0

        prev_pos ={(x,pos0[1],z):None
            for x in range(minx,maxx+1)
            for z in range(minz,maxz+1)}

        visited = {(x,pos0[1],z):False
            for x in range(minx,maxx+1)
            for z in range(minz,maxz+1)}
        #print(visited)
        search_queue.append(start_pos)
        counter = 0
        while search_queue:
            cur_block = search_queue.popleft()
            visited[cur_block] = True

            if best_dist[cur_block] > max_depth:
                continue

            neighbors = self.get_neighbors(cur_block)
            counter += 1
            print("current node: {0}".format(cur_block))
            print("neighbors: {0}".format(neighbors))
            #if counter > 100:
            #   return None
            for nb in neighbors:
                if (not visited[nb] and
                    self.is_traversable(nb) and
                    nb not in search_queue):

                    search_queue.append(nb)
                    if best_dist[cur_block] + 1 < best_dist[nb]:
                        best_dist[nb] = best_dist[cur_block] + 1
                        prev_block[nb] = cur_block
                    if nb == end_pos:
                        print("found end block neighbor")
                        break

        path = []
        cur_pos = end_pos
        if cur_pos not in prev_pos:
            return None
        #while prev_pos[cur_pos] != start_pos:
        #    path.append(prev_pos)
        print("path found: {0}".format(path))
        return path

    # returns a list of grid neighbors (diagonal movement not allowed)
    def get_neighbors(self, pos):
        x,y,z = pos
        return [(x,y,z+1),(x,y,z-1),(x+1,y,z),(x-1,y,z)]



@pl_announce('TestRoom')
class TestRoomPlugin(PluginBase):

    requires = ('Timers', 'World', 'ClientInfo', 'Event')
    #provides = 'TestRoom'
    events = {
        'world_block_update':   'handle_block_update',
    }

    # eventually __init__ will create the room
    # at a specified location
    def __init__(self, ploader, settings):
        super(TestRoomPlugin, self).__init__(ploader, settings)

        # starting location of agent
        self.dims = {
            'min_x': MIN_X,
            'min_y': MIN_Y,
            'min_z': MIN_Z,
            'max_x': MAX_X,
            'max_y': MAX_Y,
            'max_z': MAX_Z,
        }
        self.start_location = Vector3(*START_COORDS)

        # initialize the 'provides' to make this available to other plugins
        self.testroom_core = TestRoomCore(self.world, self.dims)
        ploader.provides('TestRoom',self.testroom_core)

        logger.info("test room plugin loaded")

        #frequency = 5  # in seconds
        #self.timers.reg_event_timer(frequency, self.periodic_event_handler)


    def handle_block_update(self, name, data):
        logger.info("block update data: {0}".format(data))

    def in_range(self, x, y, z):
        if (x < self.dims['min_x'] or
            x > self.dims['max_x'] or
            y < self.dims['min_y'] or
            y > self.dims['max_y'] or
            z < self.dims['min_z'] or
            z > self.dims['max_z']):
            return False
        return True
