import os
import io
import zipfile
import pyautogui
from PIL import Image

from modules.constants import SCREENSHOT_HEIGHT


def take_window_screenshot(game_window):
    """
    Takes a screenshot of the given window and returns a PIL Image object.
    """
    if not game_window:
        return None

    x, y, width, height = (
        game_window.left,
        game_window.top,
        game_window.width,
        game_window.height,
    )
    screenshot = pyautogui.screenshot(region=(x, y, width, height))

    # Resize to a fixed height if needed
    if height != SCREENSHOT_HEIGHT:
        aspect_ratio = width / height
        new_width = int(SCREENSHOT_HEIGHT * aspect_ratio)
        screenshot = screenshot.resize((new_width, SCREENSHOT_HEIGHT), Image.LANCZOS)

    return screenshot


def save_screenshot(screenshot, save_path, file_name, log):
    """
    Saves a PIL Image object to the specified ZIP archive (WebP format).
    """
    if screenshot is None:
        log.error("Screenshot is None, cannot save!")
        return

    # If the ZIP does not exist, create it
    if not os.path.exists(save_path):
        with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED):
            log.info(f"Archive created: {save_path}")

    # Append image to the ZIP
    with zipfile.ZipFile(save_path, "a", zipfile.ZIP_DEFLATED) as zip_file:
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="WebP", quality=85, optimize=True)
        img_bytes.seek(0)
        zip_file.writestr(file_name, img_bytes.getvalue())

    log.info(f"Screenshot saved: {file_name}")


def save_buffered_screenshots(
    rule_data, current_time, screenshots_buffer, screenshots_path, log
):
    """
    DRY helper that saves the last N screenshots from the ring buffer,
    where N = rule_data.get("buffer_count_before").
    """
    buffer_count = rule_data.get("buffer_count_before", 0)
    if buffer_count <= 0:
        return  # No buffer saving requested for this rule

    # Determine how many from the ring buffer we can save
    to_save = min(buffer_count, len(screenshots_buffer))
    for idx in range(to_save):
        # Grab from the end of the deque
        buff_scr = screenshots_buffer[-(idx + 1)]
        if buff_scr:
            file_name = f"{int(current_time)}_{rule_data['save_filename_prefix']}_buf{idx + 1}.png"
            save_screenshot(buff_scr, screenshots_path, file_name, log)
