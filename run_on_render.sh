export PATH="$PWD/bin:$PATH"
arduino-cli core update-index

arduino-cli config set directories.data "$PWD/arduino-data"
arduino-cli config set directories.user "$PWD/arduino-user"
arduino-cli config set directories.downloads "$PWD/arduino-downloads"

arduino-cli board listall
arduino-cli lib list

# uvicorn SweetBoxSYNTHAGE.wsgi:application --host 0.0.0.0 --port 8000
gunicorn SweetBoxSYNTHAGE.wsgi:application --bind 0.0.0.0:8000
# python manage.py runserver 0.0.0.0:8000