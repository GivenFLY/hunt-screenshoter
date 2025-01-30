import time
import psutil
import pygetwindow as gw

from modules.constants import HUNT_PROCESS_NAME, GAME_WINDOW_TITLE


def is_hunt_running():
    """
    Checks if the Hunt: Showdown process is running.
    Returns True if the process exists, otherwise False.
    """
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] and proc.info["name"].lower() == HUNT_PROCESS_NAME.lower():
            return True
    return False


def get_game_window():
    """
    Searches for the game window by title and returns it or None if not found.
    """
    windows = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
    if windows:
        return windows[0]
    return None


def wait_for_game_start(log):
    """
    Waits until the Hunt: Showdown process starts.
    """
    log.info(f"Waiting for process '{HUNT_PROCESS_NAME}' to start...")
    while True:
        if is_hunt_running():
            log.info("Game detected! Starting monitoring...")
            return
        time.sleep(2)
