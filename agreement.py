import os
import sys

agreement_text = """Agreement.

By continuing working with this script, you confirm that:
- You have read the README.md file and understand its contents.
- You acknowledge that this script is NOT an official Crytek product and has no affiliation with Hunt: Showdown or its developers.
- You understand that the script captures screenshots of the game and may upload them to a remote server for further processing.
- You accept full responsibility for using this script, including any potential violations of the game’s terms of service.

Link to README.md file: https://github.com/GivenFLY/hunt-screenshoter/blob/master/README.md

Do you agree to proceed? (y/n): """
result = input(agreement_text).lower()

if result not in ["y", "yes"]:
    print("Exiting script...")
    sys.exit()

os.system("cls" if os.name == "nt" else "clear")
