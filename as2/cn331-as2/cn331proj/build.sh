pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

python manage.py createsuperuser --username admin --email "sarasinee35584@gmail.com" --noinput