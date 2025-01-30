import time
import win32api
import win32con

from modules.constants import SCREENSHOT_RULES

# Global state to track times
last_wasd_press_time = time.time()
last_key_press_times = {}
delayed_screenshots = {}


def on_key_event(event):
    """
    Callback triggered on any keyboard event (for keys).
    Records the time of key presses for rules that rely on keyboard input.
    """
    global last_wasd_press_time

    if event.event_type == "down":
        key_name = event.name
        last_key_press_times[key_name] = time.time()

        # If it's a WASD key, record the press time
        if key_name in SCREENSHOT_RULES["WASD_MOVE"]["keys"]:
            last_wasd_press_time = time.time()

        # If it's a "delayed_key_press" (TAB), prepare for delayed screenshot
        for rule_name, rule_data in SCREENSHOT_RULES.items():
            if rule_data["type"] == "delayed_key_press":
                if key_name == rule_data["key"]:
                    delayed_screenshots[rule_name] = time.time()


def check_middle_mouse_pressed():
    """
    Checks middle mouse state with Win32.
    Returns True if pressed, False otherwise.
    """
    return win32api.GetKeyState(win32con.VK_MBUTTON) < 0
