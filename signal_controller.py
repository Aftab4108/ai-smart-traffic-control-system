# signal_controller.py

import threading
import random
from config import CONFIG


# =========================================================
# SIGNAL STATES
# =========================================================

class SignalState:

    GREEN = "GREEN"

    YELLOW = "YELLOW"

    RED = "RED"


# =========================================================
# ROAD SIGNAL OBJECT
# =========================================================

class RoadSignal:

    def __init__(self, name):

        self.name = name

        # SIGNAL INFO
        self.state = SignalState.RED

        self.countdown = 0

        self.waiting_time = 0

        # TRAFFIC INFO
        self.congestion = "LOW"

        self.score = 0

        # EMERGENCY INFO
        # emergency = True means an emergency vehicle alert is ACTIVE this tick
        self.emergency = False

        self.emergency_count = 0

        # TOTAL MAX LIMIT
        self.max_limit = random.randint(80, 120)

        # PER-TYPE MAX LIMITS (hard caps per vehicle category)
        self.type_limits = {
            "cars":   random.randint(35, 50),
            "bikes":  random.randint(25, 40),
            "buses":  random.randint(8, 15),
            "trucks": random.randint(8, 15),
        }

        # INITIAL VEHICLES
        self.vehicle_counts = {

            "cars": random.randint(10, 20),

            "bikes": random.randint(5, 15),

            "buses": random.randint(1, 4),

            "trucks": random.randint(1, 4),

            "total": 0
        }

        self.update_total()

    # =====================================================
    # UPDATE TOTAL
    # =====================================================

    def update_total(self):

        self.vehicle_counts["total"] = (

            self.vehicle_counts["cars"] +
            self.vehicle_counts["bikes"] +
            self.vehicle_counts["buses"] +
            self.vehicle_counts["trucks"]

        )


# =========================================================
# MAIN CONTROLLER
# =========================================================

class SignalController:

    def __init__(self):

        # =================================================
        # CREATE ROADS
        # =================================================

        self.roads = {

            name: RoadSignal(name)

            for name in CONFIG["road_names"]

        }

        self.lock = threading.Lock()

        # =================================================
        # SIGNAL TIMING
        # =================================================

        self.green_time = 45

        self.yellow_time = 5

        # =================================================
        # SYSTEM DATA
        # =================================================

        self.current_green = None

        self.cycle_count = 0

        self.total_vehicles_processed = 0

        self.total_emergencies = 0

        self.weather = "Sunny"

        # -------------------------------------------------
        # EMERGENCY VEHICLE LOGIC
        # -------------------------------------------------
        # Tracks which road has a pending emergency vehicle waiting.
        # Set when an emergency fires on a RED road.
        # Consumed when that road gets its next green turn.
        self.pending_emergency_road = None

        # -------------------------------------------------
        # TIMED EMERGENCY SPAWNING
        # 5 emergency vehicles total, one every 3 minutes.
        # simulation_interval = 1000 ms → 1 tick = 1 second.
        # 3 minutes = 180 ticks.
        # -------------------------------------------------
        self._ev_spawn_interval = 180   # ticks between each emergency vehicle
        self._ev_max_count      = 5     # maximum emergency vehicles to spawn
        self._ev_spawned        = 0     # how many have been spawned so far
        self._ev_tick_counter   = 0     # counts ticks since last spawn

        # =================================================
        # START FIRST SIGNAL
        # =================================================

        self._next_road()

    # =====================================================
    # DATASET COMPATIBILITY
    # =====================================================

    def update_counts(self, counts_dict):

        pass

    # =====================================================
    # PRIORITY SCORE
    # =====================================================

    def calculate_score(self, road):

        counts = road.vehicle_counts

        score = (

            counts["cars"]   * 1   +

            counts["bikes"]  * 0.5 +

            counts["buses"]  * 2   +

            counts["trucks"] * 2

        )

        return round(score, 1)

    # =====================================================
    # CONGESTION LEVEL
    # =====================================================

    def update_congestion(self, road):

        total = road.vehicle_counts["total"]

        if total <= 40:

            road.congestion = "LOW"

        elif total <= 90:

            road.congestion = "MEDIUM"

        else:

            road.congestion = "HIGH"

    # =====================================================
    # SET GREEN SIGNAL
    # =====================================================

    def _set_green(self, road_name):

        # ALL SIGNALS RED

        for road in self.roads.values():

            road.state = SignalState.RED

        # SELECT GREEN ROAD

        road = self.roads[road_name]

        road.state = SignalState.GREEN

        road.countdown = self.green_time

        self.current_green = road_name

        self.cycle_count += 1

    # =====================================================
    # SET YELLOW SIGNAL
    # =====================================================

    def _set_yellow(self, road_name):

        road = self.roads[road_name]

        road.state = SignalState.YELLOW

        road.countdown = self.yellow_time

    # =====================================================
    # PRIORITY BASED SIGNAL SELECTION
    # NO FIXED SEQUENCE
    # =====================================================

    def _next_road(self):

        # =============================================
        # EMERGENCY OVERRIDE:
        # After current signal completes (called from
        # YELLOW → RED transition), if a road has a
        # pending emergency vehicle, give it green next.
        # =============================================

        if self.pending_emergency_road and \
                self.pending_emergency_road != self.current_green:

            selected_road = self.pending_emergency_road
            self.pending_emergency_road = None
            self._set_green(selected_road)
            return

        highest_score = -1

        selected_road = None

        # =============================================
        # FIND HIGHEST PRIORITY ROAD
        # =============================================

        for road_name, road in self.roads.items():

            # SKIP CURRENT GREEN ROAD

            if road_name == self.current_green:

                continue

            # UPDATE SCORE

            road.score = self.calculate_score(road)

            # SELECT ROAD WITH HIGHEST SCORE

            if road.score > highest_score:

                highest_score = road.score

                selected_road = road_name

        # =============================================
        # SAFETY CHECK
        # =============================================

        if selected_road is None:

            selected_road = random.choice(
                list(self.roads.keys())
            )

        # =============================================
        # SET GREEN SIGNAL
        # =============================================

        self._set_green(selected_road)

    # =====================================================
    # SPAWN EMERGENCY VEHICLE (timed, max 5 total)
    # Called every tick; fires once per 180-tick interval
    # until 5 vehicles have been spawned.
    # =====================================================

    def _try_spawn_emergency_vehicle(self):

        if self._ev_spawned >= self._ev_max_count:
            return   # all 5 already spawned — stop

        self._ev_tick_counter += 1

        if self._ev_tick_counter < self._ev_spawn_interval:
            return   # not 3 minutes yet

        # 3 minutes elapsed — spawn one emergency vehicle
        self._ev_tick_counter = 0
        self._ev_spawned      += 1

        # =============================================
        # ALL 5 EVs → road with highest priority score
        # =============================================

        best_road  = None
        best_score = -1

        for road_name, road in self.roads.items():
            s = self.calculate_score(road)
            if s > best_score:
                best_score = s
                best_road  = road_name

        target_road = best_road if best_road else random.choice(list(self.roads.keys()))

        road = self.roads[target_road]

        # Mark alert active on this road
        road.emergency       = True
        road.emergency_count += 1
        self.total_emergencies += 1

        # Queue the emergency override so this road gets green
        # immediately after the current signal finishes
        if road.state == SignalState.RED:
            self.pending_emergency_road = target_road

        print(
            f"[EMERGENCY #{self._ev_spawned}] "
            f"Emergency vehicle on {target_road} road! "
            f"Will get GREEN after current signal."
        )

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def tick(self):

        with self.lock:

            # =============================================
            # RANDOM WEATHER
            # =============================================

            self.weather = random.choice([

                "Sunny",
                "Cloudy",
                "Rainy"

            ])

            # =============================================
            # TIMED EMERGENCY VEHICLE SPAWN
            # (one every 3 min, max 5 total)
            # =============================================

            self._try_spawn_emergency_vehicle()

            # =============================================
            # UPDATE ALL ROADS
            # =============================================

            for road in self.roads.values():

                # =========================================
                # RED SIGNAL
                # GRADUAL VEHICLE INCREASE WITH HARD CAPS
                # =========================================

                if road.state == SignalState.RED:

                    road.waiting_time += 1

                    # Only attempt to add if total is under max_limit
                    if road.vehicle_counts["total"] < road.max_limit:

                        # Pick only vehicle types that are BELOW their per-type cap
                        eligible = [
                            vt for vt in ["cars", "bikes", "buses", "trucks"]
                            if road.vehicle_counts[vt] < road.type_limits[vt]
                        ]

                        if eligible:

                            # Slow down additions as total approaches max_limit
                            fill_ratio = road.vehicle_counts["total"] / road.max_limit
                            add_chance = 0.90 - (fill_ratio * 0.80)

                            if random.random() < add_chance:

                                vehicle_type = random.choice(eligible)
                                road.vehicle_counts[vehicle_type] += 1

                # =========================================
                # GREEN SIGNAL
                # REMOVE 1 VEHICLE EVERY 2 SEC
                # =========================================

                elif road.state == SignalState.GREEN:

                    road.waiting_time = 0

                    if road.countdown % 2 == 0:

                        vehicle_types = []

                        if road.vehicle_counts["cars"] > 0:
                            vehicle_types.append("cars")

                        if road.vehicle_counts["bikes"] > 0:
                            vehicle_types.append("bikes")

                        if road.vehicle_counts["buses"] > 0:
                            vehicle_types.append("buses")

                        if road.vehicle_counts["trucks"] > 0:
                            vehicle_types.append("trucks")

                        # REMOVE RANDOM VEHICLE

                        if vehicle_types:

                            selected = random.choice(vehicle_types)

                            road.vehicle_counts[selected] -= 1

                            self.total_vehicles_processed += 1

                # =========================================
                # YELLOW SIGNAL
                # =========================================

                elif road.state == SignalState.YELLOW:

                    pass

                # =========================================
                # UPDATE TOTAL
                # =========================================

                road.update_total()

                # =========================================
                # UPDATE SCORE
                # =========================================

                road.score = self.calculate_score(road)

                # =========================================
                # UPDATE CONGESTION
                # =========================================

                self.update_congestion(road)

            # =============================================
            # CURRENT GREEN ROAD
            # =============================================

            current_road = self.roads[self.current_green]

            # =============================================
            # COUNTDOWN
            # =============================================

            current_road.countdown -= 1

            # =============================================
            # SIGNAL CHANGE
            # =============================================

            if current_road.countdown <= 0:

                # GREEN → YELLOW

                if current_road.state == SignalState.GREEN:

                    self._set_yellow(current_road.name)

                # YELLOW → NEXT PRIORITY ROAD
                # Emergency override checked inside _next_road()

                elif current_road.state == SignalState.YELLOW:

                    current_road.state = SignalState.RED

                    self._next_road()

            states = self._get_states()

            # =============================================
            # CLEAR EMERGENCY ALERT FLAGS AFTER SNAPSHOT
            # So GUI sees emergency=True for exactly one
            # tick; pending_emergency_road stays queued
            # until the current signal finishes.
            # =============================================

            for road in self.roads.values():
                if road.emergency:
                    road.emergency = False

            return states

    # =====================================================
    # GUI DATA
    # =====================================================

    def _get_states(self):

        return {

            name: {

                "state":        road.state,

                "countdown":    road.countdown,

                "counts":       road.vehicle_counts,

                "score":        road.score,

                "emergency":    road.emergency,

                "congestion":   road.congestion,

                "waiting_time": road.waiting_time,

                "max_limit":    road.max_limit,

                "type_limits":  road.type_limits

            }

            for name, road in self.roads.items()
        }

    # =====================================================
    # SYSTEM STATS
    # =====================================================

    def get_stats(self):

        busiest = max(

            self.roads,

            key=lambda x:
            self.roads[x].score

        )

        return {

            "cycle_count":      self.cycle_count,

            "total_vehicles":   self.total_vehicles_processed,

            "current_green":    self.current_green,

            "weather":          self.weather,

            "busiest_road":     busiest,

            "total_emergencies": self.total_emergencies,

            "ev_spawned":       self._ev_spawned,

            "ev_max":           self._ev_max_count,

        }
