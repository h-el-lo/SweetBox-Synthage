export PATH="$PWD/bin:$PATH"
# uvicorn SweetBoxSYNTHAGE.wsgi:application --host 0.0.0.0 --port 8000
# gunicorn SweetBoxSYNTHAGE.wsgi:application --bind 0.0.0.0:8000
python manage.py runserver 0.0.0.0:8000