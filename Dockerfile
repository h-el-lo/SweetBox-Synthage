# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/bin:$PATH"
ENV ARDUINO_CLI_CONFIG_FILE=/app/arduino-cli.yaml

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---------------------------
# Install Arduino CLI
# ---------------------------
RUN mkdir -p /app/bin /app/arduino-data /app/arduino-user /app/arduino-downloads && \
    curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz && \
    tar -xzf arduino-cli.tar.gz && \
    mv arduino-cli /app/bin/ && \
    rm arduino-cli.tar.gz

# Generate and modify Arduino CLI config
RUN arduino-cli config init --overwrite && \
    arduino-cli config set directories.data /app/arduino-data && \
    arduino-cli config set directories.user /app/arduino-user && \
    arduino-cli config set directories.downloads /app/arduino-downloads && \
    arduino-cli config add board_manager.additional_urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json && \
    arduino-cli config add board_manager.additional_urls https://dan.drown.org/stm32duino/package_STM32duino_index.json

# Install board cores
RUN arduino-cli core update-index && \
    arduino-cli core install arduino:avr && \
    arduino-cli core install esp32:esp32 && \
    arduino-cli core install rp2040:rp2040 && \
    arduino-cli core install stm32duino:STM32F4 && \
    arduino-cli core install stm32duino:STM32F1

# Install Arduino libraries
RUN arduino-cli lib install "MIDIUSB" && \
    arduino-cli lib install "BLE-MIDI"

# Install custom library (Adafruit_TinyUSB_MIDI)
RUN unzip ./libraries/Adafruit_TinyUSB_MIDI.zip -d /app/arduino-user/libraries/

# Collect Django static files
RUN python manage.py collectstatic --noinput

# Default command (adjust as needed)
CMD ["gunicorn", "SweetBoxSYNTHAGE.wsgi:application", "--bind", "0.0.0.0:8000"]
