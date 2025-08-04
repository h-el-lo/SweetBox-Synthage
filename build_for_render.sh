#!/bin/bash
set -e

# Directories
mkdir -p ./bin
mkdir -p ./arduino-data
mkdir -p ./arduino-user
mkdir -p ./arduino-downloads

# Download Arduino CLI
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz
tar -xzf arduino-cli.tar.gz
mv arduino-cli ./bin/

# Add to PATH
export PATH="$PWD/bin:$PATH"

# Set CLI config to use local data directory
arduino-cli config init --overwrite
arduino-cli config set directories.data "$PWD/arduino-data"
arduino-cli config set directories.user "$PWD/arduino-user"
arduino-cli config set directories.downloads "$PWD/arduino-downloads"

# Add links to board manager
arduino-cli config add board_manager.additional_urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli config add board_manager.additional_urls https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json

# Install cores
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli core install esp32:esp32
arduino-cli core install rp2040:rp2040
arduino-cli core install STMicroelectronics:stm32
arduino-cli core install stm32duino:STM32F4
arduino-cli core install stm32duino:STM32F1

# Install libraries
arduino-cli lib install "MIDIUSB"

# Confirm installations
arduino-cli core list
arduino-cli lib list
arduino-cli board listall

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput