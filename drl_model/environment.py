import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TrafficEnv(gym.Env):
    """
    Custom Environment for Smart Traffic Signal following Gymnasium interface.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, simulation=None):
        super().__init__()
        self.simulation = simulation
        
        # Action space: 0 = North, 1 = South, 2 = East, 3 = West
        self.action_space = spaces.Discrete(4)
        
        # State: [qN, qS, qE, qW, wN, wS, wE, wW, dN, dS, dE, dW]
        self.observation_space = spaces.Box(low=0.0, high=np.inf, shape=(12,), dtype=np.float32)
        
        self.state = np.zeros(12, dtype=np.float32)

    def step(self, action):
        if self.simulation:
            # step the simulation with the given action
            # e.g., self.simulation.apply_action(action)
            # self.simulation.step()
            # self.state = self.simulation.get_state()
            pass
            
        # Interpret action
        # 0 = North, 1 = South, 2 = East, 3 = West
        queue = self.state[0:4].copy()
        wait = self.state[4:8].copy()
        
        # Apply traffic dynamics: Add incoming vehicles
        queue += np.random.uniform(0.5, 1.5, size=(4,))
        wait += np.random.uniform(0.5, 1.5, size=(4,))
        
        # Apply green signal effect
        queue[action] -= 2.0
        wait[action] -= 1.0
        
        # Clip values to >= 0
        queue = np.clip(queue, 0, None)
        wait = np.clip(wait, 0, None)
        
        # Compute density
        density = queue / 20.0
        
        # Update state
        self.state = np.concatenate((queue, wait, density)).astype(np.float32)
        
        # Reward is negative total waiting time of all directions
        reward = -float(np.sum(wait))
        
        terminated = False
        truncated = False
        info = {}
        
        return self.state, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if self.simulation:
            # self.simulation.reset()
            # self.state = self.simulation.get_state()
            pass
            
        self.state = np.random.uniform(0, 10, size=(12,)).astype(np.float32)
        info = {}
        return self.state, info
