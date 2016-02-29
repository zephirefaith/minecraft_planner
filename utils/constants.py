"""
Some constants for plugins dealing with agent (discretized) movement
The agent can move forward, and can face any cardinal compass direction
(NORTH, SOUTH, EAST, WEST). These constants define values relative to
the Minecraft world
"""

# compass directions in yaw values
DIR_SOUTH = 0
DIR_EAST = 90
DIR_NORTH = 180
DIR_WEST = 270

# acceptable error to test whether agent has stopped moving
EPSILON_DIST = 1./10
EPSILON_DIR  = 90./10
