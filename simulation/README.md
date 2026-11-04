# Simulation

Use the root Start-SwarmGesture.cmd for normal formations. Runtime code is grouped
by responsibility; tests and native checks are separate and are not run at startup.
Stepped heart/wave controllers remain the physics fallback.

From the project root, in separate WSL terminals:

    bash simulation/launch/start_ros.sh preview
    bash simulation/launch/start_bridge.sh animations
    bash simulation/launch/start_markers.sh

Offline checks:

    python -m unittest discover -s simulation/tests -t . -p "test_*.py" -q

Isolated native checks in configured WSL:

    ROS_DOMAIN_ID=88 python3 -m simulation.checks.check_blended_preview
    python3 -m simulation.checks.check_continuous_backend

Do not run the manual live-preview checker alongside an interactive bridge.
