import dotenv

dotenv.load_dotenv()

# ----------------------------------------------------------------------------
# ------------------------------ CONSTANTS ------------------------------------
# ----------------------------------------------------------------------------
HUNT_PROCESS_NAME = "HuntGame.exe"
GAME_WINDOW_TITLE = "Hunt: Showdown"
SCREENSHOT_HEIGHT = 900

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
        "check_interval": 5.0,
        "condition_window": 5.0,  # If pressed within the last 5 seconds
        "save_filename_prefix": "wasd",
    },
    # 3) TAB: Take a screenshot after a 0.2-second delay and also save the last two buffers
    "TAB_SCREENSHOT": {
        "type": "delayed_key_press",
        "key": "tab",
        "delay": 0.2,  # Delay before taking the screenshot
        "buffer_count_before": 2,  # Number of buffered screenshots to save
        "save_filename_prefix": "tab",
    },
    # 4) Middle mouse button: Take an immediate screenshot (with cooldown),
    #    and also save from buffer
    "MIDDLE_MOUSE": {
        "type": "key_press_cooldown",
        "key": "middle",  # We'll handle this via win32 or keyboard
        "cooldown": 3.0,  # Cooldown period in seconds
        "buffer_count_before": 2,  # Number of buffered screenshots to save
        "save_filename_prefix": "middle_mouse",
    },
}
