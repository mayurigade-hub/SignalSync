class TrafficSignalController:
    def __init__(self, cycle_time=10):
        self.directions = ['N', 'S', 'E', 'W']
        self.current_direction = 'N'
        self.last_direction = ""
        self.signal_states = {d: 'RED' for d in self.directions}
        self.signal_states['N'] = 'GREEN'
        self.timer = 0
        self.cycle_time = cycle_time
        self.min_green_time = 5.0 # Ensure stability
        self.yellow_time = 3.0 # Fixed
        self.is_yellow = False
        self.fairness_threshold = 30.0 # Force green if wait > 30s
        self.emergency_threshold = 45.0 # Immediate priority

    def update(self, dt, scores=None, stats=None):
        self.timer += dt
        
        # 1. State machine for Signal transitions
        if not self.is_yellow:
            # NORMAL switch conditions or SMART early switch
            can_switch_early = False
            is_drl_override = False
            
            if scores and stats:
                is_drl_override = any(s >= 99999 for s in scores.values())
                curr_queue = stats[self.current_direction]['queue']
                
                # Math Mode: Early switch if lane is completely empty AND min_green_time elapsed
                if not is_drl_override and self.timer >= self.min_green_time and curr_queue == 0:
                    others_waiting = any(stats[d]['queue'] > 0 for d in self.directions if d != self.current_direction)
                    if others_waiting:
                        can_switch_early = True
                        
            if self.timer >= self.cycle_time or can_switch_early:
                self.is_yellow = True
                self.signal_states[self.current_direction] = 'YELLOW'
                self.timer = 0
        else:
            if self.timer >= self.yellow_time:
                self.signal_states[self.current_direction] = 'RED'
                self.is_yellow = False
                self.last_direction = self.current_direction
                
                if scores and stats:
                    self.current_direction = self._select_best_direction(scores, stats)
                else:
                    curr_idx = self.directions.index(self.current_direction)
                    self.current_direction = self.directions[(curr_idx + 1) % len(self.directions)]
                
                self.signal_states[self.current_direction] = 'GREEN'
                self.timer = 0

    def _select_best_direction(self, scores, stats):
        is_drl = any(s >= 99999 for s in scores.values())
        if is_drl:
            # DRL Mode: 100% Trust the score override
            return max(scores, key=scores.get)
            
        # Math Mode Below:
        final_scores = scores.copy()
        
        # 1. FAIRNESS: Check for starved lanes, but ONLY if vehicles are actually there
        starved_lanes = []
        for d in self.directions:
            if stats[d]['queue'] == 0:
                continue
                
            if stats[d]['max_wait'] >= self.emergency_threshold:
                return d # Immediate emergency priority
            if stats[d]['max_wait'] >= self.fairness_threshold:
                starved_lanes.append(d)
        
        if starved_lanes:
            return max(starved_lanes, key=lambda d: stats[d]['max_wait'])

        # 2. COOLDOWN
        if self.last_direction in final_scores:
            final_scores[self.last_direction] *= 0.1 # Heavily penalize the last green lane
            
        # 3. EMPTY LANE FILTER
        valid_lanes = [d for d in self.directions if stats[d]['queue'] > 0]
        if not valid_lanes:
            return self.current_direction # Keep current green if intersection is totally empty

        # 4. PICK WINNER
        winner = max(valid_lanes, key=lambda d: final_scores[d])
        
        # DEBUG LOGGING FOR MATH MODEL
        print("--- MATH DECISION ---")
        for d in self.directions:
            print(f"Lane {d}: Queue={stats[d]['queue']}, Wait={stats[d]['waiting_time']:.1f}, Score={final_scores.get(d, 0):.2f}")
        print(f"Winner: {winner}")
        print("---------------------")
        
        return winner

    def get_signal_color(self, direction):
        return self.signal_states[direction]
