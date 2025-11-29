"""
Hiero Review Tool - Init Script
===============================
This script is auto-loaded by Hiero/Nuke from NUKE_PATH.
It sets up the environment for the Review Tool.
"""
import sys
import os
from pathlib import Path

print("[HieroReview] init.py loading...")

# Get tool root directory (where this init.py file is located)
TOOL_ROOT = Path(__file__).parent.resolve()

# Add tool root to Python path so 'src' module can be imported
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))
    print(f"[HieroReview] Added to sys.path: {TOOL_ROOT}")

# Set environment variable for other scripts to find the tool
os.environ['HIERO_REVIEW_PATH'] = str(TOOL_ROOT)

print(f"[HieroReview] Tool initialized at: {TOOL_ROOT}")
print("[HieroReview] init.py finished loading")

