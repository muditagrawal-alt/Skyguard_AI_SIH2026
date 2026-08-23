"""
SkyGuard AI - 1-Click Master Demonstration Runner
Launches the Streamlit Interactive Control Center & Pipeline Testing UI.
"""

import sys
import os
import subprocess
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    print("=" * 70)
    print("🌦️  STARTING SKYGUARD AI REAL-TIME DEMO & CONTROL CENTER")
    print("=" * 70)
    print(f"• Project Root: {project_root}")
    print("• Launching Streamlit Interactive UI on http://localhost:8501")
    print("=" * 70)

    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false"
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 SkyGuard AI demo terminated gracefully by user.")


if __name__ == "__main__":
    main()
