import time


class FlowHoldController:
    """
    Normal:
    - base green 10s
    - extend +10s up to 90s if vehicles
    - if empty -> max 10s then rotate
    - special 90s rule: if next empty, keep current green until next has >=1

    Emergency:
    - If siren on approach i:
        ALL_YELLOW (EMERGENCY_YELLOW_SEC)
        -> ALL_RED (EMERGENCY_ALL_RED_SEC)
        -> GREEN on i until siren goes away (+ release delay)
    """

    def __init__(
        self,
        n,
        yellow=3,
        all_red=2,
        base_green=30,
        extend_step=10,
        max_green=90,
        emergency_yellow_sec=2.0,
        emergency_all_red_sec=1.0,
        emergency_release_delay_sec=3.0,
    ):
        self.n = int(n)

        self.yellow = float(yellow)
        self.all_red = float(all_red)
        self.base_green = float(base_green)
        self.extend_step = float(extend_step)
        self.max_green = float(max_green)

        self.em_yellow = float(emergency_yellow_sec)
        self.em_all_red = float(emergency_all_red_sec)
        self.em_release_delay = float(emergency_release_delay_sec)

        self.state = "GREEN"    
        self.active = 0
        self.yellow_idx = None
        self.state_end = time.time() + self.base_green

        self.green_budget = self.base_green
        self.green_start = time.time()

        self.emergency_active = False
        self.emergency_target = None
        self.emergency_last_seen = 0.0

        self._em_stage = None  

    def _now(self): return time.time()
    def _left(self): return max(0.0, self.state_end - self._now())
    def _next(self, i): return (i + 1) % self.n

    def _set(self, state, dur):
        self.state = state
        self.state_end = self._now() + float(dur)
        if state == "GREEN":
            self.green_start = self._now()
            self.green_budget = self.base_green

    def _start_emergency(self, target_idx):
        now = self._now()
        self.emergency_active = True
        self.emergency_target = int(target_idx)
        self.emergency_last_seen = now

        self._em_stage = "ALL_YELLOW"
        self.yellow_idx = None
        self._set("ALL_YELLOW", self.em_yellow)

    def _stop_emergency(self):

        self.emergency_active = False
        self.emergency_target = None
        self._em_stage = None

        if self.state == "GREEN":
            self.yellow_idx = self.active
            self._set("YELLOW", self.yellow)
        else:
            self.yellow_idx = None
            self._set("ALL_RED", self.all_red)

    def tick(self, counts, emergency_idxs=None):
        if emergency_idxs is None:
            emergency_idxs = []

        now = self._now()

        if len(counts) != self.n:
            counts = (counts[:self.n] + [0] * self.n)[:self.n]

        if emergency_idxs:
            target = int(emergency_idxs[0])

            if (not self.emergency_active) or (self.emergency_target != target):
                self._start_emergency(target)
            else:
                self.emergency_last_seen = now

        if self.emergency_active and (now - self.emergency_last_seen) >= self.em_release_delay:
            self._stop_emergency()

        if self.emergency_active:
            if now >= self.state_end:
                if self._em_stage == "ALL_YELLOW":
                    self._em_stage = "ALL_RED"
                    self._set("ALL_RED", self.em_all_red)

                elif self._em_stage == "ALL_RED":
                    self._em_stage = "GREEN"
                    self.active = self.emergency_target
                    self._set("GREEN", 1.0)  

                elif self._em_stage == "GREEN":
 
                    self.state_end = now + 1.0

            if self._em_stage == "GREEN" and self.state == "GREEN":
                if now >= self.state_end:
                    self.state_end = now + 1.0

            return {
                "state": self.state,
                "green_idx": self.active if self.state == "GREEN" else None,
                "yellow_idx": None,  
                "remaining": self._left(),
                "green_budget": self.green_budget,
                "tag": "EMERGENCY",
                "emergency_target": self.emergency_target,
            }

        cur = self.active
        nxt = self._next(cur)
        cur_count = int(counts[cur])
        nxt_count = int(counts[nxt])

        if self.state == "GREEN":
            elapsed = now - self.green_start

            if cur_count <= 0:
                if elapsed >= self.base_green:
                    self.yellow_idx = cur
                    self._set("YELLOW", self.yellow)
            else:
                if elapsed >= self.green_budget:
                    if self.green_budget < self.max_green:
                        self.green_budget = min(self.max_green, self.green_budget + self.extend_step)
                        self.state_end = self.green_start + self.green_budget
                    else:
                        if nxt_count <= 0:
                            self.state_end = now + 1.0
                        else:
                            self.yellow_idx = cur
                            self._set("YELLOW", self.yellow)

        if now >= self.state_end:
            if self.state == "YELLOW":
                self.yellow_idx = None
                self._set("ALL_RED", self.all_red)

            elif self.state == "ALL_RED":
                self.active = self._next(self.active)
                self._set("GREEN", self.base_green)

        return {
            "state": self.state,
            "green_idx": self.active if self.state == "GREEN" else None,
            "yellow_idx": self.yellow_idx if self.state == "YELLOW" else None,
            "remaining": self._left(),
            "green_budget": self.green_budget,
            "tag": "NORMAL",
            "emergency_target": None,
        }
