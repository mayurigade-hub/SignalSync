import random
import time
from simulation.vehicle import Vehicle

class TrafficGenerator:
    def __init__(self, ui_panel_width=300, sim_width=800, sim_height=800, road_width=120):
        self.ui_panel_width = ui_panel_width
        self.sim_width = sim_width
        self.sim_height = sim_height
        self.road_width = road_width
        self.center_x = ui_panel_width + sim_width // 2
        self.center_y = sim_height // 2
        
        self.vehicles_N = []
        self.vehicles_S = []
        self.vehicles_E = []
        self.vehicles_W = []
        
        self.last_spawn_time = {d: 0.0 for d in ["N", "S", "E", "W"]}
        self.scenario = "BALANCED"
        self.spawn_prob = 0.05
        self.min_spawn_interval = 1.0
        self.direction_weights = [0.25, 0.25, 0.25, 0.25] # N, S, E, W

    def set_scenario(self, scenario):
        self.scenario = scenario
        if scenario == "LOW":
            self.spawn_prob = 0.02
            self.min_spawn_interval = 2.0
            self.direction_weights = [0.25, 0.25, 0.25, 0.25]
        elif scenario == "BALANCED":
            self.spawn_prob = 0.05
            self.min_spawn_interval = 1.0
            self.direction_weights = [0.25, 0.25, 0.25, 0.25]
        elif scenario == "PEAK":
            self.spawn_prob = 0.12
            self.min_spawn_interval = 0.5
            # Heavy North-South flow
            self.direction_weights = [0.4, 0.4, 0.1, 0.1]

    def update(self, sim_time_sec):
        # Randomly choose a direction based on weights
        if random.random() < self.spawn_prob:
            d = random.choices(["N", "S", "E", "W"], weights=self.direction_weights)[0]
            if (sim_time_sec - self.last_spawn_time[d]) > self.min_spawn_interval:
                self.spawn_vehicle(d)
                self.last_spawn_time[d] = sim_time_sec

    def spawn_vehicle(self, direction):
        v_type = random.choice(["Scooter", "Car", "Car", "Bus"])
        temp = Vehicle(0, 0, direction, v_type)
        v_w, v_h = temp.width, temp.height
        
        # Lane Choice: 1 or 2
        lane = random.choice([1, 2])
        
        x, y = 0, 0
        if direction == "N": 
            # Lane 1 (Inner): center + 15 | Lane 2 (Outer): center + 45
            offset = 15 if lane == 1 else 45
            x = self.center_x + offset - v_w // 2
            y = -100
        elif direction == "S": 
            # Lane 1 (Inner): center - 15 | Lane 2 (Outer): center - 45
            offset = -15 if lane == 1 else -45
            x = self.center_x + offset - v_w // 2
            y = self.sim_height + 100
        elif direction == "E": 
            # Lane 1 (Inner): center - 15 | Lane 2 (Outer): center - 45
            offset = -15 if lane == 1 else -45
            x = self.ui_panel_width + self.sim_width + 100
            y = self.center_y + offset - v_h // 2
        elif direction == "W": 
            # Lane 1 (Inner): center + 15 | Lane 2 (Outer): center + 45
            offset = 15 if lane == 1 else 45
            x = self.ui_panel_width - 100
            y = self.center_y + offset - v_h // 2
            
        new_v = Vehicle(x, y, direction, v_type)
        
        if direction == "N": self.vehicles_N.append(new_v)
        elif direction == "S": self.vehicles_S.append(new_v)
        elif direction == "E": self.vehicles_E.append(new_v)
        elif direction == "W": self.vehicles_W.append(new_v)
