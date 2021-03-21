import numpy as np
import pathlib

# Indices of important robot properties in state.agents[car_num]
from modules.robot import Robot
from modules.waypoints.navigator import NavigationGraph
from modules.waypoints.navigator import Navigator

OWNER = 0
POS_X = 1
POS_Y = 2
ANGLE = 3
YAW = 4
BULLET_COUNT = 10

class Actor:
    def __init__(self, car_num, robot):
        self.car_num = car_num
        self.is_blue = robot.is_blue
        self.prev_commands = None
        self.next_waypoint = None
        self.destination = None
        self.nav = Navigator(pathlib.Path('modules', 'waypoints', 'data.json'))

        self.robot = robot
        self.zones = None

        # TODO replace dummy values with proper ones representing starting state
        self.next_state_commands = {}
        self.has_ammo = False
        self.not_shooting = True
        self.has_buff = False
        self.is_at_centre = False
        self.centre_waypoint = None
        self.is_at_spawn_zone = False
        self.spawn_waypoint = None
        self.buff_waypoint = None
        self.ammo_waypoint = None
    
    def commands_from_state(self, state):
        """Given the current state of the arena, determine what this robot should do next
        using a simple rule-based algorithm. These commands are represented as an array of numbers,
        which are interpreted by game.step()"""
        x = y = rotate = yaw = shoot = 1

        destination = np.array([756, 217])
        pos = self.nearest_waypoint(self.robot.center)
        dest = self.nearest_waypoint(destination)
        x, y, rotate = self.navigate(state, pos, dest, [17, 20])

        commands = [x, y, rotate, yaw, shoot]
        
        self.prev_commands = commands
        return commands


    # @arg pos should be np.array([x, y])
    def nearest_waypoint(self, pos):
        return np.argmin([np.linalg.norm(node - pos) for node in self.nav.nodes])

    def get_path(self, from_waypoint, to_waypoint, avoid_nodes=None):
        path = self.nav.navigate(from_waypoint, to_waypoint, avoid_nodes)
        return self.nav.interpolate(path, 20) if path is not None else None

    '''
        Sets the destination to the nearest waypoint, stored as the waypoint number
        @arg dest should be np.array([x, y])
    '''
    def set_destination(self, dest):
        '''Update the robots (x,y) destination co-ordinates'''
        self.destination = self.nearest_waypoint(dest)

    def navigate(self, state, from_waypoint, to_waypoint, avoid_nodes=None):
        '''Pathfind to the destination. Returns the x,y,rotation values'''
        path = self.get_path(from_waypoint, to_waypoint, avoid_nodes)
        if path is None:
            return 0, 0, 0
        target = np.array([path[0][-1], path[1][-1]])
        pos_angle = state.robots_status[0][-1]
        pos_vec = np.array([np.cos(pos_angle * np.pi / 180), np.sin(pos_angle * np.pi / 180)])
        pos = np.array(state.robots_status[0][0:2])

        for t_x, t_y in zip(path[0], path[1]):
            if np.linalg.norm(target - np.array([t_x, t_y])) < np.linalg.norm(target - pos):
                target = np.array([t_x, t_y])
                break

        print('-------')
        print(pos)
        print(target)
        target_angle = np.arctan2(target[1] - pos[1], target[0] - pos[0])
        target_vec = np.array([np.cos(target_angle), np.sin(target_angle)])
        print(pos_vec)
        print(target_vec)

        '''
        :current navigation:
        - if target is in a 90 degree cone that extends out from the front of the robot, go forward
        - else, dont move, just turn
        - angles for kernel, positive down, negative up
        '''
        turn = np.arcsin(det(pos_vec, target_vec))
        print(turn)
        if abs(turn) < 0.12:
            turn = 0

        forward = 0
        if abs(turn / np.pi * 180) < 8:
            forward = 1

        print('-------')
        return forward, 0, np.sign(turn)

    def get_property(self, state, prop):
        # TODO: Update this method to use the new standard for accessing robot properties
        return state.agents[self.car_num][prop]
    
    def take_action(self, state):
        """
        Called on every frame by the Actor, it first updates the board state as stored in Actor memory
        Then it checks the current robot state to determine what the next line of action should be.
        It then accordingly modifies the next state command that is returned to kernel on every frame
        :return: The decisions to be made in the next time frame
        """
        self.update_board_zones(state.zones)
        if self.has_ammo:
            if self.is_hp_zone_active():
                if self.has_buff:
                    if self.is_at_centre:
                        self.wait()
                    else:
                        self.move_to(self.centre_waypoint)
                else:
                    self.move_to(self.buff_waypoint)
            else:
                if self.is_at_centre:
                    self.wait()
                else:
                    self.move_to(self.centre_waypoint)
        else:
            if self.is_ammo_zone_active():
                self.rush_to(self.ammo_waypoint)
            else:
                self.rush_to(self.spawn_waypoint)

        return self.next_state_commands

    def update_board_zones(self, zones):
        """
        Updates the Actor's brain with known values of the buff/debuff zones
        :return:
        """
        """
        TODO Dummy function
        Can either be called on every 60, 120 and 180 second time mark if competition time info is passed
        to the robot, or manually checking if there is a mismatch between Actor brain and board zone's as passed in
        by outpost/competition info, and updating Actor brain accordingly
        """
        self.zones = zones

    def scan_for_enemies(self):
        """
        TODO scans the nearby vicinity of the robot using LiDAR + Camera implementation and returns a list
        of enemies that can be aimed at
        :return:
        """
        return {}

    def aim_then_shoot(self, enemies_found):
        """
        TODO Given the list of enemies that are nearby, modify the next_state_command such that the robot
        :param enemies_found:
        :return:
        """
        pass

    def wait(self):
        """
        TODO Scan's the robot's nearby environment for enemies to shoot, does not move
        :return:
        """
        scanned_enemies = self.scan_for_enemies()
        if scanned_enemies is not None:
            self.aim_then_shoot(scanned_enemies)
        else:
            # Does not make changes to next_state_command
            pass

    def move_to(self, waypoint):
        """
        TODO Scans the robot's nearby environment for enemies to shoot and sets the robots next_state_commands
        such that it moves towards its set waypoint
        :param waypoint:
        :return:
        """
        scanned_enemies = self.scan_for_enemies()
        if scanned_enemies is not None:
            self.aim_then_shoot(scanned_enemies)
        else:
            # TODO Insert navigation implementation
            # self.navigate(state, self.current_waypoint, self.destination)
            pass

    def rush_to(self, waypoint):
        """
        TODO Sets robot to navigate to the specified waypoint without checking for enemies
        :param waypoint:
        :return:
        """
        pass

    def is_ammo_zone_active(self):
        """
        TODO Checks if the supply zone is has not been activated yet from the current board zone info
        :return:
        """
        if self.is_blue:
            return self.zones.is_zone_active('ammo_blue')
        else:
            return self.zones.is_zone_active('ammo_red')

    def is_hp_zone_active(self):
        """
        TODO Checks if the ammo zone has not been activated yet from the current board zone info
        :return:
        """
        if self.is_blue:
            return self.zones.is_zone_active('hp_blue')
        else:
            return self.zones.is_zone_active('hp_red')
