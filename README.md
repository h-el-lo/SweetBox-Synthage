# SweetBox-Synthage

A Django-based web application for generating and managing MIDI controller firmware for Arduino-compatible boards. SweetBox Synthage allows users to create custom presets with knobs, buttons, and joysticks, then generate and flash firmware to various microcontroller boards.

## 🎹 Features

- **MIDI Controller Preset Management**: Create, edit, and manage custom MIDI controller configurations
- **Multi-Board Support**: Generate firmware for ATMega32U4, RP2040, and ESP32-S3 boards
- **Flexible Input Configuration**:
  - Configurable knobs with custom CC numbers, channels, and value ranges
  - Programmable buttons for notes or control changes
  - Joystick support with pitch bend or CC modes
- **Firmware Generation**: Automatic Arduino firmware generation based on preset configurations
- **User Authentication**: Secure user accounts with private preset support
- **Web-Based Interface**: Intuitive web UI for preset creation and management

## Technology Stack

- **Backend**: Django 4.2.18
- **Database**: SQLite (development) / PostgreSQL (production)
- **Web Server**: Gunicorn with Waitress
- **Arduino Integration**: arduino-cli for firmware compilation and flashing
- **Deployment**: Render.com

## Prerequisites

- Python 3.8+
- Arduino CLI
- Supported boards: ATMega32U4, RP2040, ESP32-S3

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/SweetBox-Synthage.git
   cd SweetBox-Synthage
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Arduino CLI**
   ```bash
   # Download Arduino CLI
   curl -L https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz -o arduino-cli.tar.gz
   tar -xzf arduino-cli.tar.gz
   chmod +x ./arduino-cli
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

### Production Deployment

The application is configured for deployment on Render.com. The `render.yaml` file contains the deployment configuration.

## Usage

### Creating a Preset

1. **Log in** to your account
2. **Create a new preset** with your desired configuration:
   - Number of knobs and their CC assignments
   - Button configurations (note or CC mode)
   - Joystick settings (if applicable)
   - MIDI channel assignments

### Generating Firmware

1. **Select your preset** from the dashboard
2. **Choose your target board** (ATMega32U4, RP2040, or ESP32-S3)
3. **Generate firmware** - the system will create Arduino code based on your preset
4. **Download the firmware** or flash directly to your board

### Hardware Setup

- **Knobs**: Connect potentiometers to the specified pins
- **Buttons**: Connect momentary switches to the assigned pins
- **Joystick**: Connect analog joystick to X and Y axis pins
- **MIDI Output**: The firmware will output MIDI data via USB

## Configuration

### Board Support

The application supports the following boards:
- **ATMega32U4**: Leonardo, Pro Micro, etc.
- **RP2040**: Raspberry Pi Pico, etc.
- **ESP32-S3**: Various ESP32-S3 development boards

### MIDI Configuration

- **Channels**: 1-16 (standard MIDI channels)
- **CC Numbers**: 0-127 (MIDI Control Change numbers)
- **Note Numbers**: 0-127 (MIDI note numbers)
- **Value Ranges**: 0-127 (MIDI value range)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

---

**SweetBox Synthage** - Making MIDI controller firmware generation easy and accessible.
