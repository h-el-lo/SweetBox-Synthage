export PATH="$PWD/bin:$PATH"
gunicorn SweetBoxSYNTHAGE.wsgi:application --bind 0.0.0.0:8000