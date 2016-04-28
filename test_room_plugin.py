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

START_COORDS = (-66,14,-39)

# create a dummy class to only expose certain methods
class TestRoomCore(object):
    def __init__(self, world, dims, testroom_instance):
        self.testroom_instance = testroom_instance

    def compute_path(self, pos0, pos1, max_depth=10):
        return self.testroom_instance.compute_path(pos0, pos1, max_depth)


@pl_announce('TestRoom')
class TestRoomPlugin(PluginBase):

    requires = ('Timers', 'World', 'ClientInfo', 'Event')

    events = {
        'world_block_update':   'handle_block_update',
    }

    # eventually __init__ will create the room at a specified location
    def __init__(self, ploader, settings):
        super(TestRoomPlugin, self).__init__(ploader, settings)
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
        self.testroom_core = TestRoomCore(self.world, self.dims, self)
        ploader.provides('TestRoom',self.testroom_core)
        logger.info("test room plugin loaded")

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

    def is_reachable(self, pos0, pos1):
        path = self.compute_path(pos0, pos1, max_depth=10)
        if path:
            #print("path found: {0}".format(path))
            return True
        #print("no path found")
        return False

    # note is_obstacle and is_gap ONLY WORK WITH BLOCKS SPECIFIED
    # checks the block above the given floor location to see if it is an obstacle
    def is_obstacle(self, x, y, z):
        block = self.world.get_block(x, y, z)
        # air, gold, or stone
        if block[0] != 0 and block[0] != 41 and block[0] != 1:
            return True
        return False

    # checks the given floor location to see if it is a gap
    def is_gap(self, x, y, z):
        block = self.world.get_block(x, y-1, z)
        if block[0] == 0:
            print("there is a gap with block (id,meta): {0}".format(block))
            return True
        return False

    def is_traversable(self, pos):
        x,y,z = pos
        if self.is_obstacle(x, y, z) or self.is_gap(x, y, z):
            print("block: {} is not traversable".format(pos))
            return False
        return True

    #returns a list of positions
    def compute_path(self, pos0, pos1, max_depth):
        print("start pos: {}, goal pos: {}".format(pos0, pos1))
        grnd = self.dims['min_y']
        minx = self.dims['min_x']
        maxx = self.dims['max_x']
        minz = self.dims['min_z']
        maxz = self.dims['max_z']

        start_pos = (math.floor(pos0[0]),math.floor(pos0[1]),math.floor(pos0[2]))
        end_pos = (math.floor(pos1[0]),math.floor(pos1[1]),math.floor(pos1[2]))
        goal_pos = self.get_nearest_goal(start_pos, end_pos)
        if not goal_pos:
            return None
        search_queue = coll.deque()

        best_dist ={(x, pos0[1], z):float("inf")
            for x in range(minx,maxx+1)
            for z in range(minz,maxz+1)}
        best_dist[start_pos] = 0

        prev_pos ={(x,pos0[1],z):None
            for x in range(minx,maxx+1)
            for z in range(minz,maxz+1)}
        prev_pos[start_pos] = start_pos

        visited = {(x,pos0[1],z):False
            for x in range(minx,maxx+1)
            for z in range(minz,maxz+1)}

        search_queue.append(start_pos)
        while search_queue:
            cur_block = search_queue.popleft()
            visited[cur_block] = True
            if cur_block == goal_pos:
                print("\nfound end block at cur pos\n")
                break
            neighbors = self.get_neighbors(cur_block)
            for nb in neighbors:
                #print("looking at neighbor {0}".format(nb))
                if (not visited[nb] and nb not in search_queue):
                    search_queue.append(nb)
                    if best_dist[cur_block] + 1 < best_dist[nb]:
                        #print("found better distance of {0}".format(best_dist[cur_block]+1))
                        best_dist[nb] = best_dist[cur_block] + 1
                        prev_pos[nb] = cur_block
        path = []
        cur_pos = goal_pos
        if prev_pos[cur_pos] is not None:
            while cur_pos != start_pos:
                path.append(cur_pos)
                cur_pos = prev_pos[cur_pos]
        #print("path found: {}".format(path))
        path.reverse()
        return path

    def distance(self, pos0, pos1):
        x1,y1,z1 = pos0
        x2,y2,z2 = pos1
        return math.sqrt((x2-x1)**2 + (z2-z1)**2)

    # returns a list of grid neighbors (diagonal movement not allowed)
    def get_neighbors(self, pos):
        x,y,z = pos
        neighbors = [(x,y,z+1),(x,y,z-1),(x+1,y,z),(x-1,y,z)]
        valid = [n for n in neighbors if self.in_range(*n) and self.is_traversable(n)]
        return valid

    def get_nearest_goal(self, start, end):
        neighbors = self.get_neighbors(end)
        distances = [(self.distance(start,n),n) for n in neighbors]
        if len(distances) > 0:
            return min(distances)[1]
        return None
