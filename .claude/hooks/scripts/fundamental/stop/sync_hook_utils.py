#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_hook_utils.py
Stop時にhook_utils.pyを同期
"""
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hook_utils import log_hook_execution, debug_log

def main():
    log_hook_execution()

    # scripts/hook_utils.py -> fundamental/hook_utils.py
    source = Path(__file__).parent.parent.parent / "hook_utils.py"
    dest = Path(__file__).parent.parent / "hook_utils.py"

    try:
        debug_log(f"Syncing hook_utils.py: {source} -> {dest}")
        shutil.copy2(source, dest)
        debug_log("hook_utils.py synced successfully")
    except Exception as e:
        debug_log(f"Failed to sync hook_utils.py: {e}")

if __name__ == "__main__":
    main()
