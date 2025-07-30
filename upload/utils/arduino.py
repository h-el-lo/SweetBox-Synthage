import subprocess

def check_arduino_cli_installed():
    try:
        output = subprocess.check_output(["arduino-cli", "version"], stderr=subprocess.STDOUT)
        return output.decode().strip()
    except FileNotFoundError:
        return "arduino-cli not found"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode().strip()}"
