import agreement

import os
import time
import zipfile

import keyboard
import io
import pygetwindow as gw
import pyautogui
import win32api
import win32con
from PIL import Image
import psutil
from collections import deque
from datetime import datetime

# Pynput for stable mouse handling
from pynput.mouse import Listener, Button, Controller

import dotenv
from tqdm.notebook import tqdm
from colorama import init, Fore, Style

dotenv.load_dotenv()
tqdm.pandas()
init(autoreset=True)  # Initialize colorama for colored output

# ----------------------------------------------------------------------------
# ------------------------------ CONSTANTS ------------------------------------
# ----------------------------------------------------------------------------
HUNT_PROCESS_NAME = "HuntGame.exe"
GAME_WINDOW_TITLE = "Hunt: Showdown"
SCREENSHOT_HEIGHT = 900

# Specify the root directory for saving screenshots
# (using your get_abs_data_path method from core.const).
from core.const import get_abs_screenshots_path

# Dictionary containing all screenshot conditions/binds/rules
SCREENSHOT_RULES = {
    # 1) Continuous screenshot capturing into a ring buffer
    "RING_BUFFER": {
        "type": "continuous",
        "interval": 0.2,  # Take a screenshot every 0.2 seconds
        "buffer_maxlen": 2,  # Store the last 2 screenshots
    },
    # 2) Take a screenshot every 5 seconds if the user is moving using WASD
    "WASD_MOVE": {
        "type": "conditional_interval",
        "keys": ["w", "a", "s", "d"],  # Keys to monitor for movement
        "check_interval": 5.0,  # Check every 5 seconds
        "condition_window": 5.0,  # If pressed within the last 5 seconds
        "save_filename_prefix": "wasd",
    },
    # 3) TAB: Take a screenshot after a 0.2-second delay and save the last two buffers
    "TAB_SCREENSHOT": {
        "type": "delayed_key_press",
        "key": "tab",
        "delay": 0.2,  # Delay before taking the screenshot
        "buffer_count_before": 2,  # Number of buffered screenshots to save
        "save_filename_prefix": "tab",
    },
    # 4) Middle mouse button: Take an immediate screenshot, but not more than once per second
    "MIDDLE_MOUSE": {
        "type": "key_press_cooldown",
        "key": "middle",  # We'll handle this via pynput (Button.middle)
        "cooldown": 3.0,  # Cooldown period in seconds
        "save_filename_prefix": "middle_mouse",
    },
}

# ----------------------------------------------------------------------------
# ------------------------ FUNCTIONS FOR GAME AND SCREENSHOTS ----------------
# ----------------------------------------------------------------------------


def get_game_window():
    """
    Searches for the game window by title and returns its object or None if not found.
    """
    windows = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
    if windows:
        return windows[0]
    return None


def is_hunt_running():
    """
    Checks if the Hunt: Showdown process is running.
    Returns True if the process exists, otherwise False.
    """
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] and proc.info["name"].lower() == HUNT_PROCESS_NAME.lower():
            return True
    return False


def wait_for_game_start():
    """
    Waits until the Hunt: Showdown process is started.
    """
    print(
        f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Waiting for process '{HUNT_PROCESS_NAME}' to start..."
    )
    while True:
        if is_hunt_running():
            print(
                f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Game detected! Starting monitoring..."
            )
            return
        time.sleep(2)


def take_window_screenshot():
    """
    Takes a screenshot of the game window and returns a PIL Image object in memory.
    If the game window is not found, returns None.
    """
    game_window = get_game_window()
    if not game_window:
        return None  # Avoid spamming logs if the game window isn't found
    x, y, width, height = (
        game_window.left,
        game_window.top,
        game_window.width,
        game_window.height,
    )
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    screenshot_aspect = width / height
    if height != SCREENSHOT_HEIGHT:
        new_width = int(SCREENSHOT_HEIGHT * screenshot_aspect)
        screenshot = screenshot.resize((new_width, SCREENSHOT_HEIGHT), Image.LANCZOS)
    return screenshot


def save_screenshot(screenshot, save_path, file_name):
    """
    Saves a PIL Image object to the specified file.
    """
    if screenshot is None:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Screenshot is None, cannot save!")
        return

    if not os.path.exists(save_path):
        with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED):
            print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Archive created: {save_path}")

    with zipfile.ZipFile(save_path, "a", zipfile.ZIP_DEFLATED) as zip_file:
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="WebP", quality=85, optimize=True)
        img_bytes.seek(0)
        zip_file.writestr(file_name, img_bytes.getvalue())

    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Screenshot saved: {file_name}")


# ----------------------------------------------------------------------------
# ------------------------- INITIALIZATION AND STATE --------------------------
# ----------------------------------------------------------------------------

wait_for_game_start()

# Optional global screenshot counter
screenshots_count = 0

# Initialize directory for the current session
init_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
screenshots_path = get_abs_screenshots_path(f"{init_time}.zip")

# Ring buffer for storing the latest screenshots in memory
ring_buffer_size = SCREENSHOT_RULES["RING_BUFFER"]["buffer_maxlen"]
screenshots_buffer = deque(maxlen=ring_buffer_size)

# Track the time of the last WASD key press
last_wasd_press_time = None

# Store the last press times of any keys (for cooldown checks, etc.)
last_key_press_times = {}

# For delayed screenshots (e.g., TAB), we store { rule_name: press_time, ... }
delayed_screenshots = {}

mouse = Controller()

# ----------------------------------------------------------------------------
# ------------------------ KEYBOARD EVENT HANDLER ----------------------------
# ----------------------------------------------------------------------------


def on_key_event(event):
    """
    Callback triggered on any keyboard event (for keys).
    Records the time of key presses for rules that rely on keyboard input (WASD, TAB, etc.).
    """
    global last_wasd_press_time

    if event.event_type == "down":
        key_name = event.name

        # Record the time for any key press
        last_key_press_times[key_name] = time.time()

        # If it's a WASD key, record the press time
        if key_name in SCREENSHOT_RULES["WASD_MOVE"]["keys"]:
            last_wasd_press_time = time.time()

        # If it's a "delayed_key_press" type (like TAB), prepare for delayed screenshot
        for rule_name, rule_data in SCREENSHOT_RULES.items():
            if rule_data["type"] == "delayed_key_press":
                if key_name == rule_data["key"]:
                    delayed_screenshots[rule_name] = time.time()


# Hook the keyboard event handler
keyboard.hook(on_key_event)
print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Monitoring keyboard presses...")

# ----------------------------------------------------------------------------
# ------------------------------ MAIN LOOP -----------------------------------
# ----------------------------------------------------------------------------

try:
    # Time when the next "continuous" screenshot should be taken
    next_ring_buffer_screenshot_time = time.time()
    # Time when the WASD condition was last checked
    last_wasd_check_time = time.time()

    while is_hunt_running():
        current_time = time.time()

        if win32api.GetKeyState(win32con.VK_MBUTTON) < 0:
            last_key_press_times["middle"] = time.time()

        # 1) RING_BUFFER (type = "continuous") - capture screenshots into the buffer
        ring_conf = SCREENSHOT_RULES["RING_BUFFER"]
        if current_time >= next_ring_buffer_screenshot_time:
            scr = take_window_screenshot()
            if scr:
                screenshots_buffer.append(scr)
            next_ring_buffer_screenshot_time = current_time + ring_conf["interval"]

        # 2) WASD_MOVE (type = "conditional_interval") - check user movement
        wasd_conf = SCREENSHOT_RULES["WASD_MOVE"]
        if (current_time - last_wasd_check_time) >= wasd_conf["check_interval"]:
            if last_wasd_press_time is not None:
                # If the last WASD press was within the condition window
                if (current_time - last_wasd_press_time) < wasd_conf[
                    "condition_window"
                ]:
                    scr_wasd = take_window_screenshot()
                    if scr_wasd is not None:
                        filename = f"{int(current_time)}_{wasd_conf['save_filename_prefix']}.png"
                        save_screenshot(scr_wasd, screenshots_path, filename)
            last_wasd_check_time = current_time

        # 3) TAB_SCREENSHOT (type = "delayed_key_press") - screenshot after delay
        for rule_name, press_time in list(delayed_screenshots.items()):
            rule_data = SCREENSHOT_RULES[rule_name]
            if (current_time - press_time) >= rule_data["delay"]:
                scr_now = take_window_screenshot()
                if scr_now is not None:
                    filename = (
                        f"{int(current_time)}_{rule_data['save_filename_prefix']}.png"
                    )
                    save_screenshot(scr_now, screenshots_path, filename)

                # Save buffered screenshots
                buffer_to_save = min(
                    rule_data["buffer_count_before"], len(screenshots_buffer)
                )
                for idx in range(buffer_to_save):
                    buff_scr = screenshots_buffer[-(idx + 1)]
                    if buff_scr is not None:
                        buffer_filename = f"{int(current_time)}_{rule_data['save_filename_prefix']}_buf{idx+1}.png"

                        save_screenshot(buff_scr, screenshots_path, buffer_filename)

                # Remove the rule entry to avoid repeat triggers
                delayed_screenshots.pop(rule_name, None)

        # 4) MIDDLE_MOUSE (type = "key_press_cooldown") – immediate screenshot,
        # but not more than once per cooldown period
        for rule_name, rule_data in SCREENSHOT_RULES.items():
            if rule_data["type"] == "key_press_cooldown":
                key = rule_data["key"]  # 'middle'
                if key in last_key_press_times:
                    press_time = last_key_press_times[key]
                    cooldown = rule_data["cooldown"]

                    # Use a special entry to track the last screenshot time for this rule
                    last_scr_key = f"{rule_name}_last_screenshot"
                    if last_scr_key not in last_key_press_times:
                        last_key_press_times[last_scr_key] = 0

                    last_scr_time = last_key_press_times[last_scr_key]

                    # If the mouse was pressed after the last screenshot and cooldown has passed
                    if (
                        press_time > last_scr_time
                        and (current_time - last_scr_time) >= cooldown
                    ):
                        scr_middle = take_window_screenshot()
                        if scr_middle is not None:
                            filename = f"{int(current_time)}_{rule_data['save_filename_prefix']}.png"
                            save_screenshot(scr_middle, screenshots_path, filename)
                            last_key_press_times[last_scr_key] = current_time

        # Short sleep to reduce CPU usage
        time.sleep(0.01)

except KeyboardInterrupt:
    print(f"\n{Fore.YELLOW}[INFO]{Style.RESET_ALL} Script stopped by the user.")


print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Session saved in: {screenshots_path}")
print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Game closed or script terminated.")
