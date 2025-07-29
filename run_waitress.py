from waitress import serve
from SweetBoxSYNTHAGE.wsgi import application  # Replace with your project name

serve(application, host='0.0.0.0', port=8000)
