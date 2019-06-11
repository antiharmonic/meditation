This will probably be altered into a many widget service, but for today we're going to just get meditation working
gunicorn app:app --workers 1 --bind=0.0.0.0:5732 --daemon
