python build_database.py
python api.py
gunicorn --chdir -w 2 --threads 2 --bind 0.0.0.0:5000 wsgi:app