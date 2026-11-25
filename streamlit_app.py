"""Entry point for Streamlit Community Cloud (and `streamlit run streamlit_app.py`).

It puts this folder on the import path, so TruthLayer does not need to be pip-installed,
then runs the dashboard. The dashboard opens on the saved real Blue Button run (read-only).
"""
import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
os.environ.setdefault("TRUTHLAYER_ROOT", str(HERE))

runpy.run_module("truthlayer.dashboard", run_name="__main__")
