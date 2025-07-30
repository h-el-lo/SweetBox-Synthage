FROM python:3.11-slim

# Install arduino-cli
RUN apt-get update && apt-get install -y curl tar && \
    curl -L https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz && \
    tar -xzf arduino-cli.tar.gz && \
    mv arduino-cli /usr/local/bin/arduino-cli && chmod +x /usr/local/bin/arduino-cli

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
