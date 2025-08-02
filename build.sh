#!/usr/bin/env bash
set -e

echo "Installing Arduino CLI…"
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz \
  -o arduino-cli.tar.gz
tar -xzf arduino-cli.tar.gz
chmod +x arduino-cli
mv arduino-cli /usr/local/bin/
rm arduino-cli.tar.gz

echo "Arduino CLI version:"
arduino-cli version


pip install requirements.txt
python manage.py collectstatic --noinput