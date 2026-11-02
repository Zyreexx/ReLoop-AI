#!/usr/bin/env python3
"""
ReLoop AI — Smart Hardware Diagnostics Agent (Standalone Entrypoint).
Evaluates laptop internal hardware conditions across Windows, macOS, and Linux
for circular lifecycle optimization.

Zero third-party dependencies — runs on Python 3.8+ standard library.
"""
import sys

try:
    from diagnostics_agent.runner import main
    if __name__ == "__main__":
        main()
except ImportError:
    # Fallback to self-contained execution when downloaded as standalone file
    import argparse
    import json
    import os
    import platform
    import re
    import shutil
    import subprocess
    import time
    import urllib.request
    import urllib.error

    # Add current directory and parent repository directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    try:
        from diagnostics_agent.runner import main
        if __name__ == "__main__":
            main()
    except ImportError:
        print("[!] Error: Could not locate diagnostics_agent package.")
        sys.exit(1)
