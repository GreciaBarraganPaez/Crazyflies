"""Shared project locations, independent of the invoking terminal directory."""
from pathlib import Path

SIMULATION_ROOT=Path(__file__).resolve().parents[1]
PROJECT_ROOT=SIMULATION_ROOT.parent
CONFIG_DIR=SIMULATION_ROOT/'config'
REPORTS_DIR=PROJECT_ROOT/'reports'/'simulation'
