#!/bin/bash
set -e

# Directories
mkdir -p ./bin
mkdir -p ./arduino-data

# Download Arduino CLI
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz
tar -xzf arduino-cli.tar.gz
mv arduino-cli ./bin/

# Add to PATH
export PATH="$PWD/bin:$PATH"

# Set CLI config to use local data directory
./bin/arduino-cli config init --overwrite
./bin/arduino-cli config set directories.data "$PWD/arduino-data"

# Install cores
./bin/arduino-cli core update-index
./bin/arduino-cli core install arduino:avr
./bin/arduino-cli core install esp32:esp32

# Install libraries
./bin/arduino-cli lib install "MIDIUSB"

# Confirm installations
./bin/arduino-cli core list
./bin/arduino-cli board listall

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput