#!/bin/bash

# Exit immediately if any command fails
set -e

# Download the latest Arduino CLI
echo "Downloading Arduino CLI..."
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz

# Extract the tarball
echo "Extracting Arduino CLI..."
tar -xzf arduino-cli.tar.gz

# Move the binary to /usr/local/bin
echo "Installing Arduino CLI..."
mv arduino-cli /usr/local/bin/

# Cleanup
echo "Cleaning up..."
rm arduino-cli.tar.gz

# Confirm installation
echo "Arduino CLI installed:"
arduino-cli version