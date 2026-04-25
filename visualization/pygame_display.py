import pygame

class PygameDisplay:
    def __init__(self, screen, ui_panel_width, sim_width, sim_height):
        self.screen = screen
        self.ui_panel_width = ui_panel_width
        self.sim_width = sim_width
        self.sim_height = sim_height
        self.center_x = ui_panel_width + sim_width // 2
        self.center_y = sim_height // 2
        
        # Proportional road width
        self.road_width = 120 
        
        # Colors (Premium Palette)
        self.bg_panel = (20, 20, 22)
        self.bg_sim = (24, 26, 32)
        self.color_road = (48, 50, 56)
        self.color_road_alt = (44, 46, 52) # Slight variation
        self.color_card = (32, 34, 40)
        self.color_active_green = (46, 204, 113)
        self.color_glow_green = (30, 80, 50)
        self.color_text_dim = (160, 165, 175)
        
        # Fonts
        pygame.font.init()
        self.font_header = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_card_head = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_queue = pygame.font.SysFont("Arial", 22, bold=True) # Larger Queue
        self.font_stats = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self.font_banner = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_imp = pygame.font.SysFont("Arial", 22, bold=True)
        
        # UI Layout Params (Consolidated for alignment)
        self.top_y = 75 # Standard top margin for all right-side panels
        
        # Scenario Panel Rects (Moved to Right Side)
        self.sc_width, self.sc_height = 150, 180
        self.sc_bx = self.ui_panel_width + self.sim_width - self.sc_width - 20
        self.sc_by = self.top_y
        self.btn_low = pygame.Rect(self.sc_bx + 10, self.sc_by + 40, 130, 35)
        self.btn_balanced = pygame.Rect(self.sc_bx + 10, self.sc_by + 85, 130, 35)
        self.btn_peak = pygame.Rect(self.sc_bx + 10, self.sc_by + 130, 130, 35)

    def draw_infrastructure(self, active_dir="N"):
        # 1. Background
        pygame.draw.rect(self.screen, self.bg_sim, (self.ui_panel_width, 0, self.sim_width, self.sim_height))
        
        # 2. Roads with Lane Variation
        hw = self.road_width // 2
        # Vertical Road
        pygame.draw.rect(self.screen, self.color_road, (self.center_x - hw, 0, 30, self.sim_height))
        pygame.draw.rect(self.screen, self.color_road_alt, (self.center_x - hw + 30, 0, 30, self.sim_height))
        pygame.draw.rect(self.screen, self.color_road, (self.center_x, 0, 30, self.sim_height))
        pygame.draw.rect(self.screen, self.color_road_alt, (self.center_x + 30, 0, 30, self.sim_height))
        
        # Horizontal Road
        pygame.draw.rect(self.screen, self.color_road, (self.ui_panel_width, self.center_y - hw, self.sim_width, 30))
        pygame.draw.rect(self.screen, self.color_road_alt, (self.ui_panel_width, self.center_y - hw + 30, self.sim_width, 30))
        pygame.draw.rect(self.screen, self.color_road, (self.ui_panel_width, self.center_y, self.sim_width, 30))
        pygame.draw.rect(self.screen, self.color_road_alt, (self.ui_panel_width, self.center_y + 30, self.sim_width, 30))

        # Lane Highlight (Softer)
        s = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        h_col = (46, 204, 113, 20) # Very soft green overlay
        if active_dir == 'N':
            pygame.draw.rect(s, h_col, (self.center_x, 0, hw, self.center_y - hw))
        elif active_dir == 'S':
            pygame.draw.rect(s, h_col, (self.center_x - hw, self.center_y + hw, hw, self.sim_height - (self.center_y + hw)))
        elif active_dir == 'E':
            pygame.draw.rect(s, h_col, (self.center_x + hw, self.center_y - hw, (self.ui_panel_width + self.sim_width) - (self.center_x + hw), hw))
        elif active_dir == 'W':
            pygame.draw.rect(s, h_col, (self.ui_panel_width, self.center_y, self.center_x - hw - self.ui_panel_width, hw))
        self.screen.blit(s, (0,0))

        # 3. Double Yellow divider
        yell = (200, 180, 0)
        pygame.draw.line(self.screen, yell, (self.center_x - 1, 0), (self.center_x - 1, self.sim_height), 1)
        pygame.draw.line(self.screen, yell, (self.center_x + 1, 0), (self.center_x + 1, self.sim_height), 1)
        pygame.draw.line(self.screen, yell, (self.ui_panel_width, self.center_y - 1), (self.ui_panel_width + self.sim_width, self.center_y - 1), 1)
        pygame.draw.line(self.screen, yell, (self.ui_panel_width, self.center_y + 1), (self.ui_panel_width + self.sim_width, self.center_y + 1), 1)
        
        # 4. Dashed Dividers
        dw = (160, 160, 165)
        for i in range(0, self.sim_height, 25):
            pygame.draw.line(self.screen, dw, (self.center_x - 30, i), (self.center_x - 30, i+15), 1)
            pygame.draw.line(self.screen, dw, (self.center_x + 30, i), (self.center_x + 30, i+15), 1)
        for i in range(self.ui_panel_width, self.ui_panel_width + self.sim_width, 25):
            pygame.draw.line(self.screen, dw, (i, self.center_y - 30), (i+15, self.center_y - 30), 1)
            pygame.draw.line(self.screen, dw, (i, self.center_y + 30), (i+15, self.center_y + 30), 1)

        # 5. Lane Arrows (Straight/Left/Right indication)
        arr_c = (220, 220, 220, 80) # Semi-transp
        self._draw_lane_arrows(self.center_x, self.center_y, hw)

        # 6. Stop Lines
        pygame.draw.rect(self.screen, (255, 255, 255), (self.center_x, self.center_y - hw - 3, hw, 3))
        pygame.draw.rect(self.screen, (255, 255, 255), (self.center_x - hw, self.center_y + hw, hw, 3))
        pygame.draw.rect(self.screen, (255, 255, 255), (self.center_x + hw, self.center_y - hw, 3, hw))
        pygame.draw.rect(self.screen, (255, 255, 255), (self.center_x - hw - 3, self.center_y, 3, hw))
        
        # 7. Intersection Grid
        grid_c = (100, 100, 110)
        pygame.draw.rect(self.screen, grid_c, (self.center_x - hw, self.center_y - hw, hw*2, hw*2), width=1)
        pygame.draw.line(self.screen, grid_c, (self.center_x-hw, self.center_y), (self.center_x+hw, self.center_y), 1)
        pygame.draw.line(self.screen, grid_c, (self.center_x, self.center_y-hw), (self.center_x, self.center_y+hw), 1)

    def _draw_lane_arrows(self, cx, cy, hw):
        # Helper for tiny arrows before intersection
        arrow_white = (210, 210, 215)
        # N Lane Down
        for ox in [15, 45]:
            self._arrow(cx + ox, cy - hw - 30, 0)
        # S Lane Up
        for ox in [-15, -45]:
            self._arrow(cx + ox, cy + hw + 30, 180)
        # E Lane Left
        for oy in [-15, -45]:
            self._arrow(cx + hw + 30, cy + oy, 90)
        # W Lane Right
        for oy in [15, 45]:
            self._arrow(cx - hw - 30, cy + oy, 270)

    def _arrow(self, x, y, angle):
        # Draw a tiny white arrow hint
        pts = [(0, -6), (-4, 2), (4, 2)]
        # Spin pts by angle (0=Up in localized space)
        # Actually simplest to just draw per dir
        if angle == 0: # Down (North vehicles)
            pygame.draw.polygon(self.screen, (200, 200, 205), [(x, y+6), (x-4, y-2), (x+4, y-2)])
        elif angle == 180: # Up
            pygame.draw.polygon(self.screen, (200, 200, 205), [(x, y-6), (x-4, y+2), (x+4, y+2)])
        elif angle == 90: # Left
            pygame.draw.polygon(self.screen, (200, 200, 205), [(x-6, y), (x+2, y-4), (x+2, y+4)])
        elif angle == 270: # Right
            pygame.draw.polygon(self.screen, (200, 200, 205), [(x+6, y), (x-2, y-4), (x-2, y+4)])

    def draw_traffic_lights(self, signal_controller):
        hrw = self.road_width // 2
        for d, (lx, ly) in {
            'N': (self.center_x + hrw + 12, self.center_y - hrw - 60),
            'S': (self.center_x - hrw - 32, self.center_y + hrw + 12),
            'E': (self.center_x + hrw + 12, self.center_y + hrw + 12),
            'W': (self.center_x - hrw - 32, self.center_y - hrw - 60)
        }.items():
            st = signal_controller.get_signal_color(d)
            pygame.draw.rect(self.screen, (15, 15, 18), (lx, ly, 22, 56), border_radius=6)
            rad, dy = 7, 18
            # Red
            pygame.draw.circle(self.screen, (255, 30, 30) if st == "RED" else (40, 15, 15), (lx+11, ly+11), rad)
            # Yellow
            pygame.draw.circle(self.screen, (255, 220, 0) if st == "YELLOW" else (40, 40, 15), (lx+11, ly+11+dy), rad)
            # Green
            g_col = (0, 255, 100) if st == "GREEN" else (15, 40, 15)
            pygame.draw.circle(self.screen, g_col, (lx+11, ly+11+2*dy), rad)
            if st == "GREEN": # Add highlight glow
                pygame.draw.circle(self.screen, (0, 255, 100), (lx+11, ly+11+2*dy), rad+2, width=1)

    def handle_click(self, pos):
        """Returns ('SCENARIO', scenario) or None"""
        if self.btn_low.collidepoint(pos): return ('SCENARIO', "LOW")
        if self.btn_balanced.collidepoint(pos): return ('SCENARIO', "BALANCED")
        if self.btn_peak.collidepoint(pos): return ('SCENARIO', "PEAK")
        return None

    def draw_stats_panel(self, stats, current_green):
        # Background
        pygame.draw.rect(self.screen, self.bg_panel, (0, 0, self.ui_panel_width, self.sim_height))
        # Header
        self.screen.blit(self.font_header.render("TRAFFIC CONSOLE", True, (255, 255, 255)), (25, 25))
        
        # 1. Legend (Moved back up)
        leg_y = 75
        leg_data = [((255, 255, 255), "Scooter"), ((40, 40, 40), "Car"), ((220, 30, 30), "Bus")]
        for i, (col, lab) in enumerate(leg_data):
            pygame.draw.rect(self.screen, col, (25 + i*90, leg_y, 10, 10), border_radius=2)
            self.screen.blit(self.font_small.render(lab, True, self.color_text_dim), (40 + i*90, leg_y - 2))
            if col == (40, 40, 40): # Car outline for visibility
                 pygame.draw.rect(self.screen, (100, 100, 100), (25 + i*90, leg_y, 10, 10), width=1, border_radius=2)

        # 2. Stats Cards (Shifted up)
        y, card_h = 120, 140
        for d_key, d_name in [('N', f"NORTH ({chr(8595)})"), ('S', f"SOUTH ({chr(8593)})"), ('E', f"EAST ({chr(8592)})"), ('W', f"WEST ({chr(8594)})")]:
            is_act = (d_key == current_green)
            rect = pygame.Rect(20, y, self.ui_panel_width - 40, card_h)
            pygame.draw.rect(self.screen, self.color_card, rect, border_radius=12)
            if is_act:
                pygame.draw.rect(self.screen, self.color_active_green, rect, width=2, border_radius=12)
            
            # Title
            tcol = self.color_active_green if is_act else (255, 255, 255)
            self.screen.blit(self.font_card_head.render(d_name, True, tcol), (rect.x + 20, rect.y + 15))
            
            # Data Hierarchy
            q, wr, den = stats[d_key]['queue'], stats[d_key]['waiting_time'], stats[d_key]['density']
            # 1. Queue (BOLD/LARGE)
            self.screen.blit(self.font_queue.render(f"QUEUE: {q}", True, (250, 250, 250)), (rect.x + 24, rect.y + 50))
            # 2. Waiting (MEDIUM)
            self.screen.blit(self.font_stats.render(f"WAIT: {wr:.1f}s", True, (200, 205, 215)), (rect.x + 24, rect.y + 82))
            # 3. Density (SMALLER/LIGHTER)
            self.screen.blit(self.font_small.render(f"DENSITY: {den:.2f}", True, self.color_text_dim), (rect.x + 24, rect.y + 110))
            
            y += card_h + 20

    def draw_top_banner(self, direction, state, time_left, scenario="BALANCED"):
        full = {'N': 'NORTH', 'S': 'SOUTH', 'E': 'EAST', 'W': 'WEST'}
        text_str = f"SCENARIO: {scenario} | "
        sys_str = f"SYSTEM STATUS: "
        st_text = f"{state} ({full.get(direction)})"
        next_text = f" | NEXT SWITCH: {int(time_left)}s"
        
        s0 = self.font_banner.render(text_str, True, (255, 215, 0))
        s1 = self.font_banner.render(sys_str, True, (255, 255, 255))
        s2 = self.font_banner.render(st_text, True, self.color_active_green if state == "GREEN" else (240, 60, 60))
        s3 = self.font_banner.render(next_text, True, self.color_text_dim)
        
        tw = s0.get_width() + s1.get_width() + s2.get_width() + s3.get_width()
        bx, by = self.ui_panel_width + (self.sim_width - tw - 40) // 2, 22
        pygame.draw.rect(self.screen, (25, 27, 33), (bx, by, tw+40, 42), border_radius=15)
        if state == "GREEN": pygame.draw.rect(self.screen, self.color_active_green, (bx, by, tw+40, 42), width=1, border_radius=15)
        
        self.screen.blit(s0, (bx + 20, by + 10))
        self.screen.blit(s1, (bx + 20 + s0.get_width(), by + 10))
        self.screen.blit(s2, (bx + 20 + s0.get_width() + s1.get_width(), by + 10))
        self.screen.blit(s3, (bx + 20 + s0.get_width() + s1.get_width() + s2.get_width(), by + 10))

    def draw_vehicle(self, screen, v, active_dir):
        rect = v.get_rect()
        is_active = (v.direction == active_dir)
        
        # 1. Shadow (Subtle offset)
        shadow_rect = rect.copy()
        shadow_rect.x += 2; shadow_rect.y += 2
        pygame.draw.rect(screen, (10, 10, 12, 100), shadow_rect, border_radius=3)
        
        # 2. Main Color (Brighten if active)
        base_col = v.color
        if is_active:
            # Lift color slightly
            base_col = (min(255, base_col[0] + 40), min(255, base_col[1] + 40), min(255, base_col[2] + 40))
        
        pygame.draw.rect(screen, base_col, rect, border_radius=3)
        if is_active: # Subtle glow border
            pygame.draw.rect(screen, self.color_active_green, rect, width=1, border_radius=3)
        
        # 3. Details
        if v.v_type == "Scooter":
            wheel_c = (50, 50, 50)
            if v.direction in ["N", "S"]:
                pygame.draw.circle(screen, wheel_c, (rect.centerx, rect.top+4), 3)
                pygame.draw.circle(screen, wheel_c, (rect.centerx, rect.bottom-4), 3)
            else:
                pygame.draw.circle(screen, wheel_c, (rect.left+4, rect.centery), 3)
                pygame.draw.circle(screen, wheel_c, (rect.right-4, rect.centery), 3)
        elif v.v_type == "Car":
            gray = (190, 190, 190)
            if v.direction == "N": pygame.draw.rect(screen, gray, (rect.x+2, rect.bottom-8, rect.width-4, 6))
            elif v.direction == "S": pygame.draw.rect(screen, gray, (rect.x+2, rect.top+2, rect.width-4, 6))
            elif v.direction == "E": pygame.draw.rect(screen, gray, (rect.left+2, rect.y+2, 6, rect.height-4))
            elif v.direction == "W": pygame.draw.rect(screen, gray, (rect.right-8, rect.y+2, 6, rect.height-4))
        elif v.v_type == "Bus":
            sky = (140, 190, 255)
            # 3 Windows
            if v.direction in ["N", "S"]:
                for i in range(1, 4): pygame.draw.rect(screen, sky, (rect.x+3, rect.y + i*13, rect.width-6, 7))
            else:
                for i in range(1, 4): pygame.draw.rect(screen, sky, (rect.x + i*13, rect.y+3, 7, rect.height-6))

    def draw_vehicles(self, vehicle_lists, active_dir):
        sim_rect = pygame.Rect(self.ui_panel_width + 1, 0, self.sim_width, self.sim_height)
        self.screen.set_clip(sim_rect)
        for _, v_list in vehicle_lists.items():
            for v in v_list: self.draw_vehicle(self.screen, v, active_dir)
        self.screen.set_clip(None)

    def draw_scenario_panel(self, active_scenario):
        # 1. Background Box
        pygame.draw.rect(self.screen, (28, 30, 38), (self.sc_bx, self.sc_by, self.sc_width, self.sc_height), border_radius=12)
        pygame.draw.rect(self.screen, (60, 65, 75), (self.sc_bx, self.sc_by, self.sc_width, self.sc_height), width=1, border_radius=12)
        
        # 2. Title
        txt = self.font_banner.render("TRAFFIC SCENARIO", True, (255, 255, 255))
        self.screen.blit(txt, (self.sc_bx + self.sc_width//2 - txt.get_width()//2, self.sc_by + 15))
        
        # 3. Vertical Buttons
        mouse_pos = pygame.mouse.get_pos()
        scenarios = [
            (self.btn_low, "LOW"),
            (self.btn_balanced, "BALANCED"),
            (self.btn_peak, "PEAK")
        ]
        
        for btn, label in scenarios:
            is_active = (active_scenario == label)
            is_hover = btn.collidepoint(mouse_pos)
            
            # Body
            b_col = (40, 42, 50) if not is_active else (30, 45, 40)
            if is_hover and not is_active: b_col = (55, 57, 68)
            
            pygame.draw.rect(self.screen, b_col, btn, border_radius=8)
            if is_active:
                pygame.draw.rect(self.screen, self.color_active_green, btn, width=2, border_radius=8)
            else:
                pygame.draw.rect(self.screen, (70, 75, 85), btn, width=1, border_radius=8)
            
            t_col = (255, 255, 255) if is_active else self.color_text_dim
            s_txt = self.font_stats.render(label, True, t_col)
            self.screen.blit(s_txt, (btn.centerx - s_txt.get_width()//2, btn.centery - s_txt.get_height()//2))
