"""
Private Sniper System V1.0
Main Entry Point
"""
import os
import sys

# Ensure the UI and core modules can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import SniperApp

if __name__ == "__main__":
    app = SniperApp()
    app.run()
