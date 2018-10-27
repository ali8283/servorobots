"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from https://webdocs.cs.ualberta.ca/~sutton/book/code/pole.c
"""
import os,  inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(os.path.dirname(currentdir))
os.sys.path.insert(0,parentdir)

import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import time
import subprocess
# See user manual https://usermanual.wiki/Document/pybullet20quickstart20guide.479068914.pdf
import pybullet as p
import pybullet_data
from pkg_resources import parse_version

logger = logging.getLogger(__name__)

class qt:
    def q_mult(q1, q2):
        x1, y1, z1, w1 = q1
        x2, y2, z2, w2 = q2
        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
        z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
        return x, y, z, w

    def q_conjugate(q):
        x, y, z, w = q
        return (-x, -y, -z, w)

    def qv_mult(q1, v1):
        q2 = v1 + (0.0,)
        return qt.q_mult(qt.q_mult(q1, q2), qt.q_conjugate(q1))[0:3]

class QuadcopterEnv(gym.Env):
    def __init__(self, renders=False):
        self._renders = renders
        if (renders):
            p.connect(p.GUI)
        else:
            p.connect(p.DIRECT)
        self._seed()
        # Quadcopter observation:
        # Quaternion (4)
        # Angular velocity (3), Local frame
        # Position (3)
        # Velocity (3), Local frame

        observation_dim = 13
        high_obs = np.ones([observation_dim])
        self.observation_space = spaces.Box(high_obs*0, high_obs*1.5)

        # Thrust, torque in NWU (roll, pitch, yaw). The Pixhawk is in NED, careful!
        # -1 is not thrust, + 1 is 1 g acceleration
        action_dim = 4
        act_high = np.ones([action_dim])
        self.action_space = spaces.Box(-act_high, act_high)

    def _configure(self, display=None):
        self.display = display

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _step(self, action):
        p.stepSimulation()

        # This is to controll manually the quad.
        if self._renders:
            time.sleep(self.timeStep)
            keys = p.getKeyboardEvents()
            for k, v in keys.items():

                if (k == p.B3G_RIGHT_ARROW and (v & p.KEY_WAS_TRIGGERED)):
                    turn = -0.5
                if (k == p.B3G_RIGHT_ARROW and (v & p.KEY_WAS_RELEASED)):
                    turn = 0
                if (k == p.B3G_LEFT_ARROW and (v & p.KEY_WAS_TRIGGERED)):
                    turn = 0.5
                if (k == p.B3G_LEFT_ARROW and (v & p.KEY_WAS_RELEASED)):
                    turn = 0

                if (k == p.B3G_UP_ARROW and (v & p.KEY_WAS_TRIGGERED)):
                    self.forward = 0.05
                if (k == p.B3G_UP_ARROW and (v & p.KEY_WAS_RELEASED)):
                    self.forward = 0.0
                if (k == p.B3G_DOWN_ARROW and (v & p.KEY_WAS_TRIGGERED)):
                    self.forward = -0.05
                if (k == p.B3G_DOWN_ARROW and (v & p.KEY_WAS_RELEASED)):
                    self.forward = 0.0
                #self.offset_command = self.offset_command + self.forward
                # print(self.offset_command)
                #print(keys)


        reward = 1

        #if self._renders:
            #print(math.fabs(x)/2.4)
            #print(math.fabs(self.acceleration)*1)
        world_pos, world_ori = p.getBasePositionAndOrientation(self.quad)
        world_vel, world_rot_vel = p.getBaseVelocity(self.quad)
        # world_rot_vel = (1, 0, 0)
        # To obtain local rot_vel
        _, inverse_ori = p.invertTransform([0,0,0], world_ori)


        # Expressing world rotation in quadcopter frame coordinate, required for PD controller.
        local_rot_vel = qt.qv_mult(qt.q_conjugate(world_ori), world_rot_vel)
        desired_rot_vel = np.array(action[1:4])

        rot_error = np.asarray(local_rot_vel) - desired_rot_vel

        thrust = (action[0] + 1) * self.zero_thrust


        p.applyExternalTorque(self.quad, -1, -rot_error*0.02, p.WORLD_FRAME)
        p.applyExternalForce(self.quad, -1, [0, 0, thrust], [0, 0, 0], p.LINK_FRAME)
        contacts = p.getContactPoints()

        if contacts != ():
            done = 1

        self.state =  world_pos + world_ori + world_vel + world_rot_vel
        # print(self.state)
        done = 0
        return np.array(self.state), reward, done, {}

    def _reset(self):
    #    print("-----------reset simulation---------------")
        p.resetSimulation()
        # see https://github.com/bulletphysics/bullet3/issues/1934 to load multiple colors

        rand_ori = self.np_random.uniform(low=-1, high=1, size=(4,))
        rand_ori = rand_ori/np.linalg.norm(rand_ori)


        self.quad = p.loadURDF(os.path.join(currentdir, "quad.urdf"),[0,0,0.5], rand_ori, flags=p.URDF_USE_INERTIA_FROM_FILE)

        filename = os.path.join(pybullet_data.getDataPath(), "plane_stadium.sdf")
        self.ground_plane_mjcf = p.loadSDF(filename)
        # filename = os.path.join(pybullet_data.getDataPath(),"stadium_no_collision.sdf")
        # self.ground_plane_mjcf = self._p.loadSDF(filename)
        #
        for i in self.ground_plane_mjcf:
            p.changeDynamics(i, -1, lateralFriction=0.8, restitution=0.5)
            p.changeVisualShape(i, -1, rgbaColor=[1, 1, 1, 0.8])

        self.timeStep = 0.01
        self.gravity = -9.8
        p.setGravity(0,0, self.gravity)
        # Default 0.04 for linear and angular damping.
        # p.changeDynamics(self.quad, -1, linearDamping=1)
        # p.changeDynamics(self.quad, -1, angularDamping=1)
        p.setTimeStep(self.timeStep)
        p.setRealTimeSimulation(0)

        info = p.getDynamicsInfo(self.quad, -1)
        self.mass = info[0]
        self.zero_thrust = -self.mass*self.gravity

        initialCartPos = self.np_random.uniform(low=-2, high=2, size=(1,))
        initialAngle = self.np_random.uniform(low=-0.5, high=0.5, size=(1,))
        # p.resetJointState(self.quad, 1, initialAngle)
        # p.resetJointState(self.quad, 0, initialCartPos)



        world_pos, world_ori = p.getBasePositionAndOrientation(self.quad)
        world_vel, world_rot_vel = p.getBaseVelocity(self.quad)

        self.state = world_pos + world_ori + world_vel + world_rot_vel

        return np.array(self.state)

    def _render(self, mode='human', close=False):
        return

    if parse_version(gym.__version__)>=parse_version('0.9.6'):
        render = _render
        reset = _reset
        seed = _seed
        step = _step