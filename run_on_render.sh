export PATH="$PWD/bin:$PATH"
export ARDUINO_DATA_DIR=/opt/render/.arduino15

arduino-cli board listall

# uvicorn SweetBoxSYNTHAGE.wsgi:application --host 0.0.0.0 --port 8000
# gunicorn SweetBoxSYNTHAGE.wsgi:application --bind 0.0.0.0:8000
python manage.py runserver 0.0.0.0:8000