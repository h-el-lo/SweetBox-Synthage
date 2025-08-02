export PATH="$PWD/bin:$PATH"
guniorn SweetBoxSYNTHAGE.wsgi:application --bind 0.0.0.0:8000