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

./bin/arduino-cli config add board_manager.additional_urls \
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json,\
https://www.arduino.cc/en/packages/package_index.json,\
http://arduino.esp8266.com/stable/package_esp8266com_index.json,\
https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json

./bin/arduino-cli core update-index



# ./bin/arduino-cli core install arduino:avr
# ./bin/arduino-cli core install arduino:sam
# ./bin/arduino-cli core install arduino:samd
./bin/arduino-cli core install esp32:esp32
# ./bin/arduino-cli core install STMicroelectronics:stm32



./bin/arduino-cli core list

./bin/arduino-cli board listall arduino:avr
./bin/arduino-cli board listall esp32:esp32



pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput