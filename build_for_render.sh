#!/bin/bash

set -e

# Create a local bin directory if it doesn't exist
mkdir -p ./bin

# Download and extract the latest Arduino CLI
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz
tar -xzf arduino-cli.tar.gz

# Move the binary to ./bin
mv arduino-cli ./bin/

# Optional: verify installation
./bin/arduino-cli version

# Add local bin to PATH (this will be used in the build step only)
export PATH="$PWD/bin:$PATH"

./bin/arduino-cli config init --overwrite

# Install required cores
arduino-cli core install arduino:avr
arduino-cli core install esp32:esp32

# Install required libraries
arduino-cli lib install "LibraryName"

arduino-cli board listall
arduino-cli lib listall

arduino-cli version
echo "hello"
./bin/arduino-cli version
echo "hi"

# export ARDUINO_DATA_DIR=/opt/render/.arduino15

arduino-cli config set directories.data /opt/render/.arduino15



# rm -rf $ARDUINO_DATA_DIR

# Remove problematic board URLs from config
# ./bin/arduino-cli config init --overwrite
# ./bin/arduino-cli config set board_manager.additional_urls \
# https://downloads.arduino.cc/packages/package_index.json

# ./bin/arduino-cli core install STMicroelectronics:stm32

./bin/arduino-cli core list

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput