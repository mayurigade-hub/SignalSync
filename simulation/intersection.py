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
            should_switch = False
            next_dir = None
            
            if scores and stats:
                # Dynamic Smart Mode
                best_dir = self._select_best_direction(scores, stats)
                if best_dir != self.current_direction:
                    # Only switch if min_green_time has elapsed to prevent flickering
                    if self.timer >= self.min_green_time:
                        should_switch = True
                        next_dir = best_dir
                
                # Also force switch if current lane is empty
                curr_queue = stats[self.current_direction]['queue']
                if curr_queue == 0 and self.timer >= self.min_green_time:
                    others_waiting = any(stats[d]['queue'] > 0 for d in self.directions if d != self.current_direction)
                    if others_waiting:
                        should_switch = True
                        next_dir = best_dir
            else:
                # Fallback Fixed-Cycle Mode
                if self.timer >= self.cycle_time:
                    should_switch = True
            
            if should_switch:
                self.is_yellow = True
                self.signal_states[self.current_direction] = 'YELLOW'
                self.timer = 0
                if next_dir:
                    self.next_direction = next_dir
        else:
            if self.timer >= self.yellow_time:
                self.signal_states[self.current_direction] = 'RED'
                self.is_yellow = False
                self.last_direction = self.current_direction
                
                if hasattr(self, 'next_direction'):
                    self.current_direction = self.next_direction
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
