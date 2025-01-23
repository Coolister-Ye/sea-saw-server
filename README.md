# sea-saw-server
The server side of sea-saw application, which is based on Django

## quick start
```shell script
python manage.py makemigrations
django-admin makemessages -l zh_Hans
django-admin compilemessages
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890
docker-compose -p sea_saw_dev up --build
```
