python build_database.py
#python api.py
gunicorn -w 10 --threads 10 --bind 0.0.0.0:80 wsgi:app