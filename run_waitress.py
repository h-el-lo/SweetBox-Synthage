from waitress import serve
from SweetBoxSYNTHAGE.wsgi import application  # Replace with your project name

serve(application, host='127.0.0.1', port=8000)
