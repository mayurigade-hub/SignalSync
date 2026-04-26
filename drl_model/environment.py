import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TrafficEnv(gym.Env):
    """
    Improved Traffic Environment for DQN training.
    Uses normalized states and a balanced reward function.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, simulation=None):
        super().__init__()
        self.simulation = simulation
        self.action_space = spaces.Discrete(4)
        
        # State: [4xQueue, 4xAvgWait, 4xMaxWait, 4xCurrentSignal]
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(16,), dtype=np.float32)
        
        # Internal raw state
        self.raw_queue = np.zeros(4)
        self.raw_wait_total = np.zeros(4)
        self.raw_wait_max = np.zeros(4)
        self.current_signal = 0 # 0=N, 1=S, 2=E, 3=W
        self.prev_action = -1
        self.switching_timer = 0 
        
        self.max_queue = 50.0
        self.max_avg_wait = 60.0
        self.max_max_wait = 120.0

    def _get_normalized_state(self):
        norm_q = np.clip(self.raw_queue / self.max_queue, 0, 1)
        
        avg_wait = np.zeros(4)
        for i in range(4):
            if self.raw_queue[i] > 0:
                avg_wait[i] = self.raw_wait_total[i] / self.raw_queue[i]
        
        norm_avg_w = np.clip(avg_wait / self.max_avg_wait, 0, 1)
        norm_max_w = np.clip(self.raw_wait_max / self.max_max_wait, 0, 1)
        
        # One-hot signal state
        signal_state = np.zeros(4)
        signal_state[self.current_signal] = 1.0
        
        state = np.concatenate((norm_q, norm_avg_w, norm_max_w, signal_state)).astype(np.float32)
        return state

    def step(self, action):
        # 1. Traffic Dynamics
        arrivals = np.random.poisson(0.7, size=(4,)) 
        self.raw_queue += arrivals
        
        # Increment wait times
        for i in range(4):
            if self.raw_queue[i] > 0:
                self.raw_wait_total[i] += self.raw_queue[i] * 1.0
                self.raw_wait_max[i] += 1.0
        
        # 2. Transition Logic (Yellow Light)
        if action != self.current_signal:
            self.switching_timer = 3 
            self.current_signal = action
            
        cleared = 0
        if self.switching_timer > 0:
            self.switching_timer -= 1
        else:
            # 3. Apply Green Signal
            cleared = np.random.randint(3, 7) 
            actual_cleared = min(self.raw_queue[self.current_signal], cleared)
            self.raw_queue[self.current_signal] -= actual_cleared
            
            if self.raw_queue[self.current_signal] == 0:
                self.raw_wait_total[self.current_signal] = 0
                self.raw_wait_max[self.current_signal] = 0
            else:
                self.raw_wait_total[self.current_signal] *= 0.5
            
        # 4. Reward Calculation
        # HEAVY focus on fairness and clearing long waits
        reward = (cleared * 25.0)
        reward -= np.sum(self.raw_queue) * 2.0
        reward -= np.sum(np.square(self.raw_wait_max / 30.0)) * 5.0 # Quadratic penalty for starvation!
        
        if self.switching_timer > 0:
            reward -= 60.0
        
        terminated = bool(np.any(self.raw_queue > 60))
        truncated = False
        
        return self._get_normalized_state(), float(reward), terminated, truncated, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.raw_queue = np.random.uniform(0, 15, size=(4,))
        self.raw_wait_total = self.raw_queue * np.random.uniform(0, 10, size=(4,))
        self.raw_wait_max = np.random.uniform(0, 30, size=(4,))
        self.current_signal = np.random.randint(0, 4)
        self.switching_timer = 0
        return self._get_normalized_state(), {}
