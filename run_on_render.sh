export PATH="$PWD/bin:$PATH"
arduino-cli config set directories.data /opt/render/.arduino15

arduino-cli board listall

# uvicorn SweetBoxSYNTHAGE.wsgi:application --host 0.0.0.0 --port 8000
# gunicorn SweetBoxSYNTHAGE.wsgi:application --bind 0.0.0.0:8000
python manage.py runserver 0.0.0.0:8000