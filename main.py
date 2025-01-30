import agreement
from modules.logging_setup import setup_logging
from modules.game_utils import wait_for_game_start
from modules.main_loop import main_loop


def main():
    log = setup_logging()
    log.info("Starting application...")

    # 1) Wait for the game to start
    wait_for_game_start(log)

    # 2) Run the main loop
    main_loop(log)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # In case there's an unexpected error
        _log = setup_logging(crash=True)
        _log.error(f"An error occurred: {e}")
        raise
