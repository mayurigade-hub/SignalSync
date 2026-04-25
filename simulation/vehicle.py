import pygame
import random

class Vehicle:
    def __init__(self, x, y, direction, v_type="Car"):
        self.x = x
        self.y = y
        self.direction = direction  # "N", "S", "E", "W"
        self.v_type = v_type # "Scooter", "Car", "Bus"
        self.state = "moving"
        self.waiting_time = 0.0
        
        # New Realistic Large Scale Specs
        # dimensions for N-S orientation (width x height)
        specs = {
            "Scooter": {"w": 10, "h": 20, "speed": 4.5, "color": (255, 255, 255)},
            "Car":     {"w": 16, "h": 30, "speed": 3.8, "color": (20, 20, 20)},
            "Bus":     {"w": 22, "h": 55, "speed": 2.2, "color": (220, 30, 30)}
        }
        
        spec = specs.get(v_type, specs["Car"])
        
        if direction in ["E", "W"]:
            self.width = spec["h"]
            self.height = spec["w"]
        else:
            self.width = spec["w"]
            self.height = spec["h"]
            
        self.max_speed = float(spec["speed"])
        self.current_speed = 0.0
        self.accel = 0.15
        self.color = spec["color"]

    def move(self, dt=1/60.0):
        if self.state == "moving":
            if self.current_speed < self.max_speed:
                self.current_speed += self.accel
            
            if self.direction == "N": self.y += self.current_speed
            elif self.direction == "S": self.y -= self.current_speed
            elif self.direction == "E": self.x -= self.current_speed
            elif self.direction == "W": self.x += self.current_speed
        else:
            self.current_speed = 0.0
            self.waiting_time += dt

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
