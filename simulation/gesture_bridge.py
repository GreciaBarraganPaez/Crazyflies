#!/usr/bin/env python3
"""Simulation-only receiver: UDP gesture labels -> 7 Crazyflie formations.

Start with --dry-run to test networking without ROS. --run-sim connects to
Crazyswarm2; launch the Crazyflie server with backend:=sim first.

The keyboard in this terminal is an independent human-controlled landing path.
This is a teaching prototype, NOT a real-flight safety controller.
"""
from __future__ import annotations

import argparse
import select
import socket
import sys
import time

from formations import DRONES, FLIGHT_HEIGHT, positions, check_geometry

PORT = 5055
TAKEOFF_SEC = 3.0
MOVE_SEC = 6.0
LAND_SEC = 3.0
MARGIN_SEC = 1.0
GESTURES = {"one", "peace", "three", "ok", "palm", "fist"}
ACTIONS = {
    "one": "takeoff", "peace": "v", "three": "line",
    "ok": "circle", "palm": "land", "fist": "hover (no new motion)",
}


class SimulationController:
    """Manual-arm simulation controller with cooldown and a controlled landing."""

    def __init__(self, swarm):
        self.swarm = swarm
        self.by_name = swarm.allcfs.crazyfliesByName
        if set(self.by_name) != set(DRONES):
            raise RuntimeError(
                f"Expected {sorted(DRONES)}, got {sorted(self.by_name)}. "
                "Regenerate the seven-drone simulation config."
            )
        self.state = "grounded"
        self.armed = False
        self.busy_until = 0.0

    def update(self):
        if time.monotonic() < self.busy_until:
            return
        if self.state in ("taking_off", "moving"):
            self.state = "airborne"
        elif self.state == "landing":
            self.state = "grounded"
            self.armed = False

    def arm(self):
        self.update()
        if self.state != "grounded":
            print("Arm ignored: land first.", flush=True)
            return
        self.armed = True
        print("ARMED for ONE simulated takeoff. Show 'one' (index finger) to take off.", flush=True)

    def land(self, reason="land"):
        self.update()
        self.armed = False
        if self.state in ("grounded", "landing"):
            print(f"{reason}: already grounded/landing; disarmed.", flush=True)
            return
        print(f"{reason}: controlled landing (not motor emergency stop).", flush=True)
        self.swarm.allcfs.land(targetHeight=0.04, duration=LAND_SEC)
        self.state = "landing"
        self.busy_until = time.monotonic() + LAND_SEC + MARGIN_SEC

    def handle(self, label):
        self.update()
        if label == "palm":
            self.land("Open palm")  # Priority over motion gating.
            return
        if label == "fist":
            print("Fist: no new movement command. Existing trajectory is NOT interrupted.", flush=True)
            return
        if label == "one":
            if self.state != "grounded" or not self.armed:
                print("Takeoff ignored: already flying or not armed (press a + Enter).", flush=True)
                return
            self.armed = False
            self.swarm.allcfs.takeoff(targetHeight=FLIGHT_HEIGHT, duration=TAKEOFF_SEC)
            self.state = "taking_off"
            self.busy_until = time.monotonic() + TAKEOFF_SEC + MARGIN_SEC
            print(f"Takeoff commanded: {FLIGHT_HEIGHT} m", flush=True)
            return
        if self.state != "airborne":
            print(f"{label}: ignored while {self.state}; wait until movement finishes.", flush=True)
            return
        formation = {"peace": "v", "three": "line", "ok": "circle"}[label]
        for drone, goal in positions(formation).items():
            self.by_name[drone].goTo(list(goal), yaw=0.0, duration=MOVE_SEC)
        self.state = "moving"
        self.busy_until = time.monotonic() + MOVE_SEC + MARGIN_SEC
        print(f"Commanded formation: {formation.upper()} ({MOVE_SEC:.0f} s)", flush=True)


def parse_gesture(data):
    if len(data) > 32:
        return None
    try:
        label = data.decode("ascii", errors="strict").strip().lower()
    except UnicodeDecodeError:
        return None
    return label if label in GESTURES else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print commands without connecting to ROS")
    mode.add_argument("--run-sim", action="store_true", help="Connect to simulated Crazyflies only")
    parser.add_argument("--bind", default="0.0.0.0", help="IPv4 listen address (0.0.0.0 for WSL NAT)")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--allowed-ip", help="Optional Windows host IP; reject packets from other IPs")
    args, extra = parser.parse_known_args()
    if extra and extra[0] != "--ros-args":
        parser.error(f"Unexpected extra arguments: {extra}")
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535")

    controller = None
    if args.run_sim:
        check_geometry()  # Geometric targets; NOT flight collision validation.
        from crazyflie_py import Crazyswarm  # Import ROS only when actually needed.
        print("SIMULATION ONLY. Ensure ROS server was launched with backend:=sim.", flush=True)
        controller = SimulationController(Crazyswarm())

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((args.bind, args.port))
        server.settimeout(0.15)
        print(f"Listening on UDP {args.bind}:{args.port} | mode={'SIM' if controller else 'DRY RUN'}", flush=True)
        if controller:
            print("Commands in THIS terminal: 'a' + Enter = arm takeoff, 'x' + Enter = land/disarm, 'q' + Enter = quit.", flush=True)
        else:
            print("Send test labels from Windows; no ROS or drones are required.", flush=True)
        try:
            while True:
                if controller:
                    controller.update()
                if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.readline().strip().lower()
                    if key == "q":
                        break
                    if controller and key == "a":
                        controller.arm()
                    elif controller and key in ("x", "land"):
                        controller.land("Keyboard")
                try:
                    data, peer = server.recvfrom(1024)
                except socket.timeout:
                    continue
                if args.allowed_ip and peer[0] != args.allowed_ip:
                    print(f"Blocked packet from {peer[0]}", flush=True)
                    continue
                gesture = parse_gesture(data)
                if gesture is None:
                    print("Ignored unknown UDP payload", flush=True)
                    continue
                if controller:
                    print(f"Received {gesture} from {peer[0]} -> {ACTIONS[gesture]}", flush=True)
                    controller.handle(gesture)
                else:
                    print(f"DRY RUN {peer[0]}: {gesture} -> {ACTIONS[gesture]}", flush=True)
        except KeyboardInterrupt:
            print("\nInterrupted.", flush=True)
        finally:
            if controller and controller.state not in ("grounded", "landing"):
                controller.land("Shutdown")
                # Sim only: allow a commanded landing to finish before process exits.
                time.sleep(LAND_SEC + MARGIN_SEC)
            print("Bridge stopped.", flush=True)


if __name__ == "__main__":
    main()
