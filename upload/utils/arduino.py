# utils/arduino.py
import subprocess

def check_installed():
    """
    Checks if arduino-cli is installed and available in the system PATH.

    Returns:
        tuple: (is_installed (bool), message (str))
    """
    try:
        result = subprocess.run(
            ["arduino-cli", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except FileNotFoundError:
        return False, "arduino-cli is not found. Please install it and ensure it is in your PATH."
    except subprocess.CalledProcessError as e:
        return False, f"Error executing arduino-cli: {e.stderr.strip() if e.stderr else 'Unknown error'}"
