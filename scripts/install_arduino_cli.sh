#!/bin/bash

# Exit on error
set -e

# Download the latest Arduino CLI
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz

# Extract it
tar -xzf arduino-cli.tar.gz

# Move the binary to a directory in PATH
sudo mv arduino-cli /usr/local/bin/

# Clean up
rm arduino-cli.tar.gz

# Optionally check version (debug log)
arduino-cli version