#!/bin/bash

echo "Installing Arduino CLI..."
curl -L https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz
tar -xzf arduino-cli.tar.gz
mv arduino-cli ./arduino-cli
chmod +x ./arduino-cli