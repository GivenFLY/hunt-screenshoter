import time
from collections import deque
from datetime import datetime

import keyboard

from modules.constants import SCREENSHOT_RULES
from modules.event_handler import (
    on_key_event,
    check_middle_mouse_pressed,
    delayed_screenshots,
)

import modules.event_handler

from modules.game_utils import is_hunt_running, get_game_window
from modules.screenshot_utils import (
    take_window_screenshot,
    save_screenshot,
    save_buffered_screenshots,
)

from core.const import get_abs_screenshots_path


def main_loop(log):
    """
    Main logic that runs until the game closes or user stops the script.
    """
    # 1) Hook the keyboard event handler
    keyboard.hook(on_key_event)
    log.info("Monitoring keyboard presses...")

    # 2) Prepare ring buffer for continuous screenshots
    ring_buffer_size = SCREENSHOT_RULES["RING_BUFFER"]["buffer_maxlen"]
    screenshots_buffer = deque(maxlen=ring_buffer_size)

    # 3) Initialize path for the ZIP of screenshots
    init_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    screenshots_path = get_abs_screenshots_path(f"{init_time}.zip")

    # 4) Time trackers
    next_ring_buffer_screenshot_time = time.time()
    last_wasd_check_time = time.time()

    try:
        while is_hunt_running():
            current_time = time.time()

            # Check middle mouse button (using Win32)
            if check_middle_mouse_pressed():
                # If pressed, record press time in the last_key_press_times
                modules.event_handler.last_key_press_times["middle"] = current_time

            # --------------------------------------------------------------------
            # 1) RING_BUFFER: continuous capture
            # --------------------------------------------------------------------
            ring_conf = SCREENSHOT_RULES["RING_BUFFER"]
            if current_time >= next_ring_buffer_screenshot_time:
                game_window = get_game_window()
                scr = take_window_screenshot(game_window)
                if scr:
                    screenshots_buffer.append(scr)
                next_ring_buffer_screenshot_time = current_time + ring_conf["interval"]

            # --------------------------------------------------------------------
            # 2) WASD_MOVE: conditional interval
            # --------------------------------------------------------------------
            wasd_conf = SCREENSHOT_RULES["WASD_MOVE"]
            if (current_time - last_wasd_check_time) >= wasd_conf["check_interval"]:
                if (
                    current_time - modules.event_handler.last_wasd_press_time
                ) < wasd_conf["condition_window"]:
                    game_window = get_game_window()
                    scr_wasd = take_window_screenshot(game_window)
                    if scr_wasd:
                        fname_wasd = f"{int(current_time)}_{wasd_conf['save_filename_prefix']}.png"
                        save_screenshot(scr_wasd, screenshots_path, fname_wasd, log)
                last_wasd_check_time = current_time

            # --------------------------------------------------------------------
            # 3) TAB_SCREENSHOT: delayed key press
            # --------------------------------------------------------------------
            for rule_name, press_time in list(delayed_screenshots.items()):
                rule_data = SCREENSHOT_RULES[rule_name]
                if (current_time - press_time) >= rule_data["delay"]:
                    # Take immediate screenshot
                    game_window = get_game_window()
                    scr_now = take_window_screenshot(game_window)
                    if scr_now:
                        fname_tab = f"{int(current_time)}_{rule_data['save_filename_prefix']}.png"
                        save_screenshot(scr_now, screenshots_path, fname_tab, log)

                    # Save ring buffer screenshots (DRY!)
                    save_buffered_screenshots(
                        rule_data,
                        current_time,
                        screenshots_buffer,
                        screenshots_path,
                        log,
                    )

                    # Remove this delayed screenshot entry
                    delayed_screenshots.pop(rule_name, None)

            # --------------------------------------------------------------------
            # 4) MIDDLE_MOUSE: cooldown press
            # --------------------------------------------------------------------
            for rule_name, rule_data in SCREENSHOT_RULES.items():
                if rule_data["type"] == "key_press_cooldown":
                    key = rule_data["key"]  # 'middle'
                    if key in modules.event_handler.last_key_press_times:
                        press_time = modules.event_handler.last_key_press_times[key]
                        cooldown = rule_data["cooldown"]

                        # Track the last screenshot time for this rule separately
                        last_scr_key = f"{rule_name}_last_screenshot"
                        if (
                            last_scr_key
                            not in modules.event_handler.last_key_press_times
                        ):
                            modules.event_handler.last_key_press_times[last_scr_key] = 0

                        last_scr_time = modules.event_handler.last_key_press_times[
                            last_scr_key
                        ]

                        # If cooldown is satisfied AND there's a new press
                        if (press_time > last_scr_time) and (
                            (current_time - last_scr_time) >= cooldown
                        ):
                            game_window = get_game_window()
                            scr_middle = take_window_screenshot(game_window)
                            if scr_middle:
                                fname_middle = f"{int(current_time)}_{rule_data['save_filename_prefix']}.png"
                                save_screenshot(
                                    scr_middle, screenshots_path, fname_middle, log
                                )

                                # DRY! Also save ring buffer
                                save_buffered_screenshots(
                                    rule_data,
                                    current_time,
                                    screenshots_buffer,
                                    screenshots_path,
                                    log,
                                )

                                # Update last screenshot time
                                modules.event_handler.last_key_press_times[
                                    last_scr_key
                                ] = current_time

            # Short sleep to reduce CPU usage
            time.sleep(0.01)

    except KeyboardInterrupt:
        log.info("Script stopped by the user.")

    log.info(f"Session saved in: {screenshots_path}")
    log.info("Game closed or script terminated.")
