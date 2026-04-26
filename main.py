import pygame
import sys
import torch
import os

from simulation.traffic_generator import TrafficGenerator
from simulation.intersection import TrafficSignalController
from mathematical_model.prediction import predict_queue
from mathematical_model.scoring_model import calculate_score
from visualization.pygame_display import PygameDisplay
from drl_model.agent import DQNAgent
import time
import random
import math
import torch.nn.functional as F

class MetricsTracker:
    def __init__(self, print_interval=30.0, name="TRACKER"):
        self.name = name
        self.print_interval = print_interval
        self.reset()
        
    def reset(self):
        self.total_wait_time = 0.0
        self.max_wait_time = 0.0
        self.total_vehicles_passed = 0
        self.total_queue_length = 0
        self.frames = 0
        self.last_print_time = time.time()

    def update(self, current_frame_wait_time, vehicles_passed_this_frame, current_frame_queue_len):
        self.total_wait_time += current_frame_wait_time
        if current_frame_wait_time > self.max_wait_time:
            self.max_wait_time = current_frame_wait_time
        self.total_vehicles_passed += vehicles_passed_this_frame
        self.total_queue_length += current_frame_queue_len
        self.frames += 1
        
        if time.time() - self.last_print_time >= self.print_interval:
            self.print_results()

    def get_stats(self):
        avg_wait_time = self.total_wait_time / max(1, self.total_vehicles_passed)
        avg_queue = self.total_queue_length / max(1, self.frames)
        return {
            "avg_wait": avg_wait_time,
            "max_wait": self.max_wait_time,
            "throughput": self.total_vehicles_passed,
            "avg_queue": avg_queue
        }

    def print_results(self):
        stats = self.get_stats()
        print(f"\n===== {self.name} RESULTS =====")
        print(f"Average Wait Time : {stats['avg_wait']:.1f} seconds")
        print(f"Max Wait Time     : {stats['max_wait']:.1f} seconds")
        print(f"Throughput        : {stats['throughput']} vehicles")
        print(f"Avg Queue Length  : {stats['avg_queue']:.1f}")
        print("===============================\n")
        self.last_print_time = time.time()

# ---------------- CONFIG ----------------
UI_PANEL_WIDTH = 300
SIM_WIDTH = 800
SIM_HEIGHT = 800
TOTAL_WIDTH = UI_PANEL_WIDTH + SIM_WIDTH
ROAD_WIDTH = 120

STOP_LINES = {
    'N': 340,
    'S': 460,
    'E': 760,
    'W': 640
}

# ---------------- MAIN ----------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((TOTAL_WIDTH, SIM_HEIGHT))
    pygame.display.set_caption("Smart Traffic Sim - DRL vs Math")
    clock = pygame.time.Clock()

    generator = TrafficGenerator(UI_PANEL_WIDTH, SIM_WIDTH, SIM_HEIGHT, ROAD_WIDTH)
    signal_controller = TrafficSignalController(cycle_time=8)
    display = PygameDisplay(screen, UI_PANEL_WIDTH, SIM_WIDTH, SIM_HEIGHT)

    # ---------------- DRL SETUP ----------------
    drl_mode = True  # CHANGE THIS TO SWITCH

    agent = DQNAgent(state_size=16, action_size=4)
    model_path = "drl_model/dqn_agent.pth"
    
    if os.path.exists(model_path):
        agent.q_network.load_state_dict(torch.load(model_path, map_location=agent.device))
        print(f"[SUCCESS] Loaded DRL model from {model_path}")
    else:
        print("[ERROR] DRL model not found. Using random weights")

    agent.q_network.eval()

    lane_mapping = {0: 'N', 1: 'S', 2: 'E', 3: 'W'}

    scenario = "BALANCED"
    running = True
    drl_tracker = MetricsTracker(print_interval=30.0, name="DRL")
    math_tracker = MetricsTracker(print_interval=30.0, name="MATH")

    # ---------------- DRL FALLBACK VARS ----------------
    drl_last_action = -1
    drl_stuck_counter = 0
    drl_fallback_timer = 0

    # ---------------- PLAYBACK STATE VARS ----------------
    experiment_duration = 60.0
    sim_state = "IDLE" # States: IDLE, RUNNING_MATH, RUNNING_DRL, RESULTS
    sim_time_sec = 0.0
    current_screen = "menu"
    menu_scroll_offset = 0.0
    menu_grid_drift = 0.0
    fade_in_alpha = 0
    import random
    particles = [{'x': random.uniform(0, TOTAL_WIDTH), 'y': random.uniform(0, SIM_HEIGHT), 'speed': random.uniform(10, 30), 'size': random.uniform(1, 3), 'alpha': random.uniform(50, 150)} for _ in range(40)]

    while running:
        dt = clock.get_time() / 1000.0

        if current_screen == "menu":
            # ---------------- UPDATE MENU STATE ----------------
            if fade_in_alpha < 255:
                fade_in_alpha = min(255, fade_in_alpha + 5)
            
            menu_grid_drift += 15.0 * dt
            if menu_grid_drift > 80.0:
                menu_grid_drift -= 80.0
                
            for p in particles:
                p['y'] -= p['speed'] * dt
                if p['y'] < -10:
                    p['y'] = SIM_HEIGHT + 10
                    p['x'] = random.uniform(0, TOTAL_WIDTH)
            
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_click = True

            # --- Define Layout Constants ---
            content_y = 160
            btn_y = content_y + 400
            
            # Define GET STARTED Button Rect
            get_started_rect = pygame.Rect(TOTAL_WIDTH//2 - 110, btn_y - 30, 220, 60)
            is_hover = get_started_rect.collidepoint(mouse_pos)
            
            if is_hover and mouse_click:
                current_screen = "simulation"

            # ---------------- DRAW MENU ----------------
            # 1. Background Gradient (Deep Navy)
            for i in range(SIM_HEIGHT):
                r = max(11, 19 - int(i * 8 / SIM_HEIGHT))
                g = max(15, 26 - int(i * 11 / SIM_HEIGHT))
                b = max(26, 43 - int(i * 17 / SIM_HEIGHT))
                pygame.draw.line(screen, (r, g, b), (0, i), (TOTAL_WIDTH, i))

            # 2. Animated Grid
            grid_color = (30, 45, 80)
            for x in range(-80, TOTAL_WIDTH + 80, 80):
                pygame.draw.line(screen, grid_color, (x + menu_grid_drift, 0), (x + menu_grid_drift, SIM_HEIGHT), 1)
            for y in range(0, SIM_HEIGHT, 80):
                pygame.draw.line(screen, grid_color, (0, y), (TOTAL_WIDTH, y), 1)
                
            # 3. Floating Particles
            for p in particles:
                p_surf = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (200, 220, 255, int(p['alpha'] * (fade_in_alpha/255))), (p['size'], p['size']), p['size'])
                screen.blit(p_surf, (p['x'], p['y']))

            # ---------------- HIERARCHY & LAYOUT ----------------
            
            # 1. BRAND TITLE (SignalSync - Top Center)
            brand_font = pygame.font.SysFont("Arial", 36, bold=True)
            b1 = brand_font.render("Signal", True, (240, 240, 240))
            b2 = brand_font.render("Sync", True, (245, 158, 11))
            b_w = b1.get_width() + b2.get_width()
            b_x = TOTAL_WIDTH//2 - b_w//2
            b_y = 50
            b1.set_alpha(int(fade_in_alpha * 0.8))
            b2.set_alpha(int(fade_in_alpha * 0.8))
            screen.blit(b1, (b_x, b_y))
            screen.blit(b2, (b_x + b1.get_width(), b_y))
            
            # 2. MAIN HERO CLUSTER
            # Main Title
            title_font_lg = pygame.font.SysFont("Arial", 64, bold=True)
            title_font_sm = pygame.font.SysFont("Arial", 42, bold=True)
            
            t1 = title_font_lg.render("SMART ", True, (255, 255, 255))
            t2 = title_font_lg.render("TRAFFIC", True, (245, 158, 11))
            
            t_w = t1.get_width() + t2.get_width()
            start_x = TOTAL_WIDTH//2 - t_w//2
            
            t1.set_alpha(fade_in_alpha)
            t2.set_alpha(fade_in_alpha)
            screen.blit(t1, (start_x, content_y))
            screen.blit(t2, (start_x + t1.get_width(), content_y))
            
            t3 = title_font_sm.render("CONTROL SYSTEM", True, (255, 255, 255))
            t3.set_alpha(fade_in_alpha)
            screen.blit(t3, (TOTAL_WIDTH//2 - t3.get_width()//2, content_y + 70))
            
            # 3. SUBTITLE
            sub_font = pygame.font.SysFont("Arial", 18)
            sub_text = "Benchmarking Mathematical Model vs Deep Reinforcement Learning"
            sub_t = sub_font.render(sub_text, True, (160, 170, 190))
            sub_t.set_alpha(int(fade_in_alpha * 0.7))
            screen.blit(sub_t, (TOTAL_WIDTH//2 - sub_t.get_width()//2, content_y + 140))
            
            # 4. VISUAL FOCUS ELEMENT (Animated Intersection)
            import math
            pulse = (math.sin(pygame.time.get_ticks() / 400.0) + 1) / 2
            
            cx, cy = TOTAL_WIDTH//2, content_y + 240
            
            # Glowing base
            glow_radius = int(50 + pulse * 15)
            glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (245, 158, 11, 30), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (cx - glow_radius, cy - glow_radius))
            
            # Crossing lines
            pygame.draw.line(screen, (80, 100, 140), (cx - 60, cy), (cx + 60, cy), 2)
            pygame.draw.line(screen, (80, 100, 140), (cx, cy - 60), (cx, cy + 60), 2)
            
            # Nodes with pulse
            node_color = (245, 158, 11)
            for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
                nx = cx + math.cos(angle) * 50
                ny = cy + math.sin(angle) * 50
                n_size = 6 + pulse * 3
                n_glow = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(n_glow, (245, 158, 11, 100), (10, 10), 10)
                screen.blit(n_glow, (nx - 10, ny - 10))
                pygame.draw.circle(screen, node_color, (int(nx), int(ny)), int(n_size))

            # 5. BUTTON
            btn_scale = 1.05 if is_hover else 1.0
            btn_w = int(220 * btn_scale)
            btn_h = int(60 * btn_scale)
            btn_rect_draw = pygame.Rect(TOTAL_WIDTH//2 - btn_w//2, btn_y - btn_h//2, btn_w, btn_h)
            
            # Shadow
            shadow_rect = btn_rect_draw.move(0, 4)
            pygame.draw.rect(screen, (5, 8, 15), shadow_rect, border_radius=12)
            
            # Button Glow
            glow_val = int(40 + pulse * 20) if is_hover else 30
            btn_glow = pygame.Surface((btn_w + 30, btn_h + 30), pygame.SRCALPHA)
            pygame.draw.rect(btn_glow, (245, 158, 11, glow_val), btn_glow.get_rect(), border_radius=15)
            screen.blit(btn_glow, (btn_rect_draw.x - 15, btn_rect_draw.y - 15))
            
            btn_color = (251, 191, 36) if is_hover else (245, 158, 11)
            pygame.draw.rect(screen, btn_color, btn_rect_draw, border_radius=12)
            
            btn_font = pygame.font.SysFont("Arial", 22, bold=True)
            btn_t = btn_font.render("GET STARTED", True, (11, 15, 26))
            screen.blit(btn_t, btn_t.get_rect(center=btn_rect_draw.center))
            
            # 6. BOTTOM SIGNAL INDICATOR
            strip_y = SIM_HEIGHT - 80
            colors = [(239, 68, 68), (245, 158, 11), (34, 197, 94)]
            for i, color in enumerate(colors):
                lx = TOTAL_WIDTH//2 + (i - 1) * 60
                is_on = True
                if i == 0 and (pygame.time.get_ticks() // 800) % 3 == 0: is_on = False
                if i == 1 and (pygame.time.get_ticks() // 400) % 4 == 0: is_on = False
                if i == 2 and (pygame.time.get_ticks() // 600) % 5 == 0: is_on = False
                
                final_color = color if is_on else tuple(c//4 for c in color)
                if is_on:
                    l_glow = pygame.Surface((30, 30), pygame.SRCALPHA)
                    pygame.draw.circle(l_glow, (*color, 60), (15, 15), 15)
                    screen.blit(l_glow, (lx - 15, strip_y - 15))
                pygame.draw.circle(screen, final_color, (lx, strip_y), 12)
                pygame.draw.circle(screen, (255, 255, 255, 100), (lx, strip_y), 12, 1)

            pygame.display.flip()
            clock.tick(60)
            continue

        # ---------------- EVENTS ----------------
        # Define Playback Controls UI Panel (Bottom Right)
        panel_w, panel_h = 260, 140
        panel_x = TOTAL_WIDTH - panel_w - 20
        panel_y = SIM_HEIGHT - panel_h - 80 
        
        # Split panel into Time Control (top) and Start (bottom)
        time_ctrl_rect = pygame.Rect(panel_x, panel_y, panel_w, 50)
        btn_minus_rect = pygame.Rect(panel_x + 15, panel_y + 10, 40, 30)
        btn_plus_rect = pygame.Rect(panel_x + panel_w - 55, panel_y + 10, 40, 30)
        
        start_test_btn_rect = pygame.Rect(panel_x, panel_y + 50, panel_w, 90)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if sim_state == "RESULTS" and (event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE):
                    sim_state = "IDLE" # Close UI dashboard
                elif sim_state == "IDLE":
                    # Allow keyboard input for timer
                    if event.key == pygame.K_UP or event.key == pygame.K_RIGHT:
                        experiment_duration = min(300.0, experiment_duration + 10.0)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_LEFT:
                        experiment_duration = max(10.0, experiment_duration - 10.0)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if sim_state == "RESULTS":
                    continue  # Ignore interactions behind the overlay screen!
                    
                if sim_state == "IDLE" and btn_minus_rect.collidepoint(event.pos):
                    experiment_duration = max(10.0, experiment_duration - 10.0)
                elif sim_state == "IDLE" and btn_plus_rect.collidepoint(event.pos):
                    experiment_duration = min(300.0, experiment_duration + 10.0)
                elif sim_state == "IDLE" and start_test_btn_rect.collidepoint(event.pos):
                    sim_state = "RUNNING_MATH"
                    import random
                    random.seed(42) # Ensure deterministic traffic
                    sim_time_sec = 0.0
                    drl_mode = False
                    math_tracker.reset()
                    drl_tracker.reset()
                    generator.vehicles_N.clear()
                    generator.vehicles_S.clear()
                    generator.vehicles_E.clear()
                    generator.vehicles_W.clear()
                    generator.last_spawn_time = {d: 0.0 for d in ["N", "S", "E", "W"]}
                    signal_controller.timer = 0
                    signal_controller.is_yellow = False
                    signal_controller.current_direction = 'N'
                    signal_controller.last_direction = ""
                    signal_controller.signal_states = {d: 'RED' for d in ['N', 'S', 'E', 'W']}
                    signal_controller.signal_states['N'] = 'GREEN'
                else:
                    click_info = display.handle_click(event.pos)
                    if click_info:
                        msg_type, val = click_info
                        if msg_type == 'SCENARIO' and sim_state == "IDLE":
                            scenario = val
                            generator.set_scenario(scenario)

        # ---------------- STATE MACHINE ADVANCEMENT ----------------
        if sim_state == "RUNNING_MATH":
            sim_time_sec += dt
            generator.update(sim_time_sec)
            if sim_time_sec >= experiment_duration:
                # Math run finished, transition to DRL
                sim_state = "RUNNING_DRL"
                import random
                random.seed(42) # Exactly the same seed for DRL run!
                sim_time_sec = 0.0
                drl_mode = True
                generator.vehicles_N.clear()
                generator.vehicles_S.clear()
                generator.vehicles_E.clear()
                generator.vehicles_W.clear()
                generator.last_spawn_time = {d: 0.0 for d in ["N", "S", "E", "W"]}
                signal_controller.timer = 0
                signal_controller.is_yellow = False
                signal_controller.current_direction = 'N'
                signal_controller.last_direction = ""
                signal_controller.signal_states = {d: 'RED' for d in ['N', 'S', 'E', 'W']}
                signal_controller.signal_states['N'] = 'GREEN'
                drl_stuck_counter = 0
                drl_fallback_timer = 0
                drl_last_action = -1
                
        elif sim_state == "RUNNING_DRL":
            sim_time_sec += dt
            generator.update(sim_time_sec)
            if sim_time_sec >= experiment_duration:
                sim_state = "RESULTS"

        all_vehs = {
            'N': generator.vehicles_N,
            'S': generator.vehicles_S,
            'E': generator.vehicles_E,
            'W': generator.vehicles_W
        }

        # ---------------- STATS ----------------
        stats, scores = {}, {}

        for d, v_list in all_vehs.items():
            if d == 'N':
                waiting = [v for v in v_list if v.y < STOP_LINES['N']]
            elif d == 'S':
                waiting = [v for v in v_list if v.y > STOP_LINES['S']]
            elif d == 'E':
                waiting = [v for v in v_list if v.x > STOP_LINES['E']]
            else:
                waiting = [v for v in v_list if v.x < STOP_LINES['W']]

            queue = sum(1 for v in waiting if v.state == "stopped")
            total_wait = sum(v.waiting_time for v in waiting)
            max_wait = max([v.waiting_time for v in waiting] + [0.0])

            density = len(v_list) / 400.0

            stats[d] = {
                'queue': queue,
                'waiting_vehicles': len(waiting),
                'waiting_time': total_wait,
                'max_wait': max_wait,
                'density': density
            }

            scores[d] = calculate_score(
                queue,
                total_wait,
                predict_queue(queue, 0.05),
                weights=[0.9, 0.1, 0.0]
            )

        # ---------------- DRL LOGIC ----------------
        if drl_mode:
            # State: 4xQueue, 4xAvgWait, 4xMaxWait, 4xCurrentSignal
            MAX_QUEUE = 50.0
            MAX_AVG_WAIT = 60.0
            MAX_MAX_WAIT = 120.0
            
            def get_norm(val, cap): return min(val / cap, 1.0)
            
            norm_state = []
            # 1. Queues
            for d in ['N', 'S', 'E', 'W']:
                norm_state.append(get_norm(stats[d]['queue'], MAX_QUEUE))
            
            # 2. Avg Waits
            for d in ['N', 'S', 'E', 'W']:
                q = max(1, stats[d]['queue'])
                avg_w = stats[d]['waiting_time'] / q
                norm_state.append(get_norm(avg_w, MAX_AVG_WAIT))
                
            # 3. Max Waits
            for d in ['N', 'S', 'E', 'W']:
                norm_state.append(get_norm(stats[d]['max_wait'], MAX_MAX_WAIT))
                
            # 4. Current Signal (One-hot)
            curr_dir = signal_controller.current_direction
            dirs = ['N', 'S', 'E', 'W']
            for d in dirs:
                norm_state.append(1.0 if d == curr_dir else 0.0)
            
            state_tensor = torch.FloatTensor(norm_state).unsqueeze(0).to(agent.device)

            with torch.no_grad():
                q_values = agent.q_network(state_tensor)

            import random
            import torch.nn.functional as F
            
            # --- HYBRID INTELLIGENT CONTROLLER ---
            q_vals_masked = q_values.clone()
            
            # --- HYSTERESIS / STABILITY FILTER ---
            # Boost current lane's Q-value to prevent flickering every frame
            curr_dir = signal_controller.current_direction
            curr_idx = ['N', 'S', 'E', 'W'].index(curr_dir)
            # Q-values are typically negative. We ADD absolute value to boost it positively.
            q_vals_masked[0][curr_idx] += abs(q_vals_masked[0][curr_idx].item()) * 0.20
            waitings = [stats['N']['waiting_vehicles'], stats['S']['waiting_vehicles'], stats['E']['waiting_vehicles'], stats['W']['waiting_vehicles']]
            
            # 1. SAFETY FILTER: Mask empty lanes
            valid_lanes = []
            for i in range(4):
                if waitings[i] == 0:
                    q_vals_masked[0][i] = -999999.0  # Reject empty lanes completely
                else:
                    valid_lanes.append(i)

            # 2. DRL PRIMARY DECISION (Argmax)
            action = torch.argmax(q_vals_masked).item()
            chosen_dir = lane_mapping[action]
            
            # 3. PRIORITY CORRECTION (The Hybrid Override)
            max_waiting = max(waitings)
            
            # Only trigger priority check if there's actually traffic
            if max_waiting > 0:
                max_lane_idx = waitings.index(max_waiting)
                drl_selected_waiting = waitings[action]
                
                # RELAXED: If the DRL selects a lane that has less than 30% of the maximum waiting traffic...
                if drl_selected_waiting < (max_waiting * 0.3):
                    # Override the DRL! The congestion difference is too severe to ignore.
                    original_action = action
                    action = max_lane_idx
                    chosen_dir = lane_mapping[action]
                    
                    # Print clearly without spamming too constantly
                    if getattr(agent, "debug_frame", 0) % 60 == 0:
                        print(f"[HYBRID OVERRIDE] DRL chose {lane_mapping[original_action]} ({drl_selected_waiting} veh) but {chosen_dir} has critical congestion ({max_waiting} veh)!")

                    
            # 3. Validation Logging (Print approx 1x per second)
            agent.debug_frame = getattr(agent, "debug_frame", 0) + 1
            if agent.debug_frame % 60 == 0:
                print("\n===== DRL DEBUG VALIDATION =====")
                print(f"Norm NQueue: {norm_state[0]:.2f} | NWait: {norm_state[4]:.2f}")
                print(f"Norm SQueue: {norm_state[1]:.2f} | SWait: {norm_state[5]:.2f}")
                print(f"Norm EQueue: {norm_state[2]:.2f} | EWait: {norm_state[6]:.2f}")
                print(f"Norm WQueue: {norm_state[3]:.2f} | WWait: {norm_state[7]:.2f}")
                print(f"Q VALUES: {q_values.cpu().numpy()}")
                print(f"ACTION: {action} ({chosen_dir})")
                print("================================\n")
                
            # Override scoring → force DRL decision
            scores = {d: 0 for d in ['N', 'S', 'E', 'W']}
            scores[chosen_dir] = 999999

        # ---------------- SIGNAL UPDATE ----------------
        if sim_state in ["RUNNING_MATH", "RUNNING_DRL"]:
            signal_controller.update(dt, scores=scores, stats=stats)

        # ---------------- VEHICLE MOVEMENT ----------------
        vehicles_passed_this_frame = 0
        for d, v_list in all_vehs.items():
            # Sort Front-to-Back to process collisions correctly
            if d == 'N': v_list.sort(key=lambda v: v.y, reverse=True)
            elif d == 'S': v_list.sort(key=lambda v: v.y)
            elif d == 'E': v_list.sort(key=lambda v: v.x)
            elif d == 'W': v_list.sort(key=lambda v: v.x, reverse=True)

            for i, v in enumerate(v_list):
                sig = signal_controller.get_signal_color(d)
                should_stop = False
                
                # 1. Stop Line Physics
                if sig != "GREEN":
                    if d == 'N' and (v.y + v.height) >= STOP_LINES['N'] - 5 and (v.y + v.height) < STOP_LINES['N']: should_stop = True
                    elif d == 'S' and v.y <= STOP_LINES['S'] + 5 and v.y > STOP_LINES['S']: should_stop = True
                    elif d == 'E' and v.x <= STOP_LINES['E'] + 5 and v.x > STOP_LINES['E']: should_stop = True
                    elif d == 'W' and (v.x + v.width) >= STOP_LINES['W'] - 5 and (v.x + v.width) < STOP_LINES['W']: should_stop = True
                
                # 2. Vehicle Collision Physics
                for j in range(i-1, -1, -1):
                    front_v = v_list[j]
                    # Ensure they are in the same exact lane (x-coord or y-coord)
                    if d in ['N', 'S'] and abs(v.x - front_v.x) < 20:
                        if d == 'N' and front_v.y - (v.y + v.height) < 15: should_stop = True
                        elif d == 'S' and v.y - (front_v.y + front_v.height) < 15: should_stop = True
                        break # Found nearest front vehicle
                    elif d in ['E', 'W'] and abs(v.y - front_v.y) < 20:
                        if d == 'E' and v.x - (front_v.x + front_v.width) < 15: should_stop = True
                        elif d == 'W' and front_v.x - (v.x + v.width) < 15: should_stop = True
                        break

                v.state = "stopped" if should_stop else "moving"
                if sim_state in ["RUNNING_MATH", "RUNNING_DRL"]:
                    v.move(dt)

            # ---------------- GARBAGE COLLECTION ----------------
            # Delete vehicles that have driven off-screen to prevent memory leaks!
            EXIT_THRESHOLD = 200
            valid = [ve for ve in v_list if (-EXIT_THRESHOLD < ve.x < TOTAL_WIDTH + EXIT_THRESHOLD and
                                             -EXIT_THRESHOLD < ve.y < SIM_HEIGHT + EXIT_THRESHOLD)]
            
            vehicles_passed_this_frame += (len(v_list) - len(valid))

            if sim_state in ["RUNNING_MATH", "RUNNING_DRL"]:
                if d == 'N': generator.vehicles_N = valid
                elif d == 'S': generator.vehicles_S = valid
                elif d == 'E': generator.vehicles_E = valid
                elif d == 'W': generator.vehicles_W = valid

        # Update Tracker metrics
        if sim_state in ["RUNNING_MATH", "RUNNING_DRL"]:
            total_wait_frame = sum(stats[d]['waiting_time'] for d in stats)
            current_total_q = sum(stats[d]['queue'] for d in stats)
            if drl_mode:
                drl_tracker.update(total_wait_frame, vehicles_passed_this_frame, current_total_q)
            else:
                math_tracker.update(total_wait_frame, vehicles_passed_this_frame, current_total_q)

        # =========================================================
        # ---------------- DASHBOARD RENDER OVERLAY ---------------
        # =========================================================
        if sim_state == "RESULTS":
            screen.fill((20, 20, 24)) # Deep dashboard backdrop
            
            dash_font_title = pygame.font.SysFont('segoeui', 34, bold=True)
            dash_font_head = pygame.font.SysFont('segoeui', 22, bold=True)
            dash_font_body = pygame.font.SysFont('consolas', 18)
            dash_font_large = pygame.font.SysFont('segoeui', 36, bold=True)
            
            # --- Title Row ---
            screen.blit(dash_font_title.render("SIMULATION EXPERIMENT DASHBOARD", True, (255, 255, 255)), (40, 40))
            screen.blit(dash_font_head.render(f"DURATION PER MODEL: {experiment_duration:.1f} sec", True, (180, 180, 180)), (TOTAL_WIDTH - 380, 50))
            
            math_stats = math_tracker.get_stats()
            drl_stats = drl_tracker.get_stats()
            
            m_col_x = 80
            d_col_x = 550
            mid_y = 120
            box_width = 420
            
            # MATH Headers
            pygame.draw.rect(screen, (35, 35, 45), (m_col_x - 20, mid_y, box_width, 180), border_radius=12)
            pygame.draw.rect(screen, (50, 150, 255), (m_col_x - 20, mid_y, box_width, 6)) # Blue Header Line
            screen.blit(dash_font_head.render("LEFT: MATH RESULT", True, (200, 220, 255)), (m_col_x, mid_y + 20))
            
            m_text_lines = [
                f"Average Wait Time : {math_stats['avg_wait']:.1f} sec",
                f"Max Wait Time     : {math_stats['max_wait']:.1f} sec",
                f"Throughput        : {math_stats['throughput']} vehicles",
                f"Avg Queue Length  : {math_stats['avg_queue']:.1f}"
            ]
            for i, line in enumerate(m_text_lines):
                screen.blit(dash_font_body.render(line, True, (200, 200, 200)), (m_col_x, mid_y + 60 + i*25))
                
            # DRL Headers
            pygame.draw.rect(screen, (35, 45, 35), (d_col_x - 20, mid_y, box_width, 180), border_radius=12)
            pygame.draw.rect(screen, (0, 255, 128), (d_col_x - 20, mid_y, box_width, 6)) # Green Header Line
            screen.blit(dash_font_head.render("RIGHT: DRL RESULT", True, (200, 255, 200)), (d_col_x, mid_y + 20))

            d_text_lines = [
                f"Average Wait Time : {drl_stats['avg_wait']:.1f} sec",
                f"Max Wait Time     : {drl_stats['max_wait']:.1f} sec",
                f"Throughput        : {drl_stats['throughput']} vehicles",
                f"Avg Queue Length  : {drl_stats['avg_queue']:.1f}"
            ]
            for i, line in enumerate(d_text_lines):
                screen.blit(dash_font_body.render(line, True, (200, 200, 200)), (d_col_x, mid_y + 60 + i*25))
                
            # --- Comparison Table ---
            tab_y = 330
            tab_x = 180
            pygame.draw.rect(screen, (30, 30, 35), (tab_x, tab_y, 700, 220), border_radius=12)
            pygame.draw.rect(screen, (80, 80, 90), (tab_x, tab_y, 700, 220), width=2, border_radius=12)
            
            col_headers = ["Metric", "Math", "DRL"]
            metrics_rows = [
                ["Avg Wait Time", f"{math_stats['avg_wait']:.1f}", f"{drl_stats['avg_wait']:.1f}"],
                ["Max Wait Time", f"{math_stats['max_wait']:.1f}", f"{drl_stats['max_wait']:.1f}"],
                ["Throughput", f"{math_stats['throughput']}", f"{drl_stats['throughput']}"],
                ["Avg Queue", f"{math_stats['avg_queue']:.1f}", f"{drl_stats['avg_queue']:.1f}"]
            ]
            
            c0, c1, c2 = tab_x + 40, tab_x + 300, tab_x + 500
            screen.blit(dash_font_head.render(col_headers[0], True, (255, 255, 255)), (c0, tab_y + 20))
            screen.blit(dash_font_head.render(col_headers[1], True, (150, 200, 255)), (c1, tab_y + 20))
            screen.blit(dash_font_head.render(col_headers[2], True, (150, 255, 180)), (c2, tab_y + 20))
            pygame.draw.line(screen, (100, 100, 110), (tab_x + 20, tab_y + 60), (tab_x + 680, tab_y + 60), 2)
            
            for i, r in enumerate(metrics_rows):
                ry = tab_y + 80 + i * 35
                screen.blit(dash_font_body.render(r[0], True, (220, 220, 220)), (c0, ry))
                screen.blit(dash_font_body.render(r[1], True, (220, 220, 220)), (c1, ry))
                screen.blit(dash_font_body.render(r[2], True, (220, 220, 220)), (c2, ry))

            # --- Conclusion Section ---
            con_y = 600
            screen.blit(dash_font_head.render("FINAL CONCLUSION", True, (200, 200, 200)), (c0, con_y))
            
            # Automated Winner logic
            # In modern traffic engineering, Average Wait Time is the primary metric for smart controllers.
            better_model = "MATH"
            better_color = (150, 200, 255)
            
            # DRL wins if it provides a better (lower) average wait time
            if drl_stats['avg_wait'] < math_stats['avg_wait']:
                better_model = "DRL"
                better_color = (0, 255, 128)
            # Or if it has drastically better throughput
            elif drl_stats['throughput'] > math_stats['throughput'] * 1.05:
                better_model = "DRL"
                better_color = (0, 255, 128)
                
            screen.blit(dash_font_large.render(f"Better Performance: {better_model}", True, better_color), (c0, con_y + 30))
            
            # --- Back Footer ---
            screen.blit(dash_font_body.render("[ Press ESC to return to simulation ]", True, (100, 100, 100)), (TOTAL_WIDTH // 2 - 160, SIM_HEIGHT - 40))

            pygame.display.flip()
            clock.tick(60)
            continue # Skip rendering the physical traffic simulation frame!

        # ---------------- DRAW ----------------
        screen.fill((20, 20, 20))

        display.draw_infrastructure(signal_controller.current_direction)
        display.draw_traffic_lights(signal_controller)
        display.draw_vehicles(all_vehs, signal_controller.current_direction)
        display.draw_stats_panel(stats, signal_controller.current_direction)
        display.draw_top_banner(signal_controller.current_direction, 
                              signal_controller.get_signal_color(signal_controller.current_direction), 
                              max(0, signal_controller.cycle_time - signal_controller.timer), scenario)
        display.draw_scenario_panel(scenario)

        # ---------------- DRAW UI OVERLAY ----------------
        ui_font = pygame.font.SysFont('segoeui', 20, bold=True)
        timer_font = pygame.font.SysFont('consolas', 20, bold=True)
        
        # Get mouse state for hover/click tactile effects
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]

        # Draw Control Panel Background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        # Background shadow/glow
        pygame.draw.rect(screen, (10, 10, 12), panel_rect.inflate(8, 8), border_radius=14)
        # Main panel
        pygame.draw.rect(screen, (35, 35, 40), panel_rect, border_radius=14)
        # Inner border
        pygame.draw.rect(screen, (70, 70, 80), panel_rect, width=2, border_radius=14)

        if sim_state == "IDLE":
            # Draw Time Control UI (-10s / +10s)
            # Minus Button
            m_hover = btn_minus_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (80, 80, 90) if m_hover else (50, 50, 60), btn_minus_rect, border_radius=6)
            if m_hover: pygame.draw.rect(screen, (200, 200, 200), btn_minus_rect, width=2, border_radius=6)
            m_lbl = ui_font.render("-10", True, (255, 255, 255))
            m_lrect = m_lbl.get_rect(center=btn_minus_rect.center)
            if m_hover and mouse_click: m_lrect.y += 1
            screen.blit(m_lbl, m_lrect)

            # Plus Button
            p_hover = btn_plus_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (80, 80, 90) if p_hover else (50, 50, 60), btn_plus_rect, border_radius=6)
            if p_hover: pygame.draw.rect(screen, (200, 200, 200), btn_plus_rect, width=2, border_radius=6)
            p_lbl = ui_font.render("+10", True, (255, 255, 255))
            p_lrect = p_lbl.get_rect(center=btn_plus_rect.center)
            if p_hover and mouse_click: p_lrect.y += 1
            screen.blit(p_lbl, p_lrect)
            
            # Time Display
            time_disp = ui_font.render(f"SET TIME: {int(experiment_duration)}s", True, (255, 200, 100))
            screen.blit(time_disp, time_disp.get_rect(center=(time_ctrl_rect.centerx, time_ctrl_rect.centery)))

            # Draw Start Test Button
            hover = start_test_btn_rect.collidepoint(mouse_pos)
            color = (0, 200, 100) if hover else (0, 150, 80)
            if hover and mouse_click:
                color = (0, 100, 50)
            
            pygame.draw.rect(screen, color, start_test_btn_rect, border_radius=14)
            if hover:
                pygame.draw.rect(screen, (255, 255, 255), start_test_btn_rect, width=2, border_radius=14)
                
            start_lbl = ui_font.render("START EXPERIMENT", True, (255, 255, 255))
            start_lrect = start_lbl.get_rect(center=start_test_btn_rect.center)
            if hover and mouse_click: start_lrect.y += 2
            screen.blit(start_lbl, start_lrect)
            
        else:
            # Draw Experiment Progress
            state_text = "Running Math..." if sim_state == "RUNNING_MATH" else "Running DRL..."
            state_color = (255, 140, 0) if sim_state == "RUNNING_MATH" else (0, 255, 128)
            
            lbl = ui_font.render(state_text, True, state_color)
            lbl_rect = lbl.get_rect(centerx=panel_rect.centerx, top=panel_rect.top + 20)
            screen.blit(lbl, lbl_rect)
            
            # Progress Bar
            progress = min(1.0, sim_time_sec / experiment_duration)
            bar_w = panel_w - 40
            bar_h = 15
            bar_x = panel_rect.left + 20
            bar_y = panel_rect.top + 60
            
            pygame.draw.rect(screen, (20, 20, 25), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            pygame.draw.rect(screen, state_color, (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=5)
            
            # Time Text
            time_str = f"{sim_time_sec:.1f} / {experiment_duration:.1f}s"
            t_lbl = timer_font.render(time_str, True, (255, 255, 255))
            t_rect = t_lbl.get_rect(centerx=panel_rect.centerx, top=bar_y + 25)
            screen.blit(t_lbl, t_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()