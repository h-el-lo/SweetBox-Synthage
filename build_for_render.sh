#!/bin/bash

set -e

# Create a local bin directory if it doesn't exist
mkdir -p ./bin

# Download and extract the latest Arduino CLI
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz
tar -xzf arduino-cli.tar.gz

# Move the binary to ./bin
mv arduino-cli ./bin/

# Add local bin to PATH (this will be used in the build step only)
export PATH="$PWD/bin:$PATH"

# Optional: verify installation
./bin/arduino-cli version

arduino-cli core install arduino:avr
arduino-cli core install esp32:esp32

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput