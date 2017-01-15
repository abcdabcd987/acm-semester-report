# acm-semester-report
Website for submitting ACM Honored Class semester report

## Setup

Postfix mail service needed.

```bash
sudo apt install p7zip-full
sudo pip install -r requirements.txt
sudo python maintenance.py initdb
```

## Run Web Server

```bash
# debug
python application.py

# production
gunicorn -b 127.0.0.1:5001 --access-logfile - application:app
```

## Maintenance

```bash
python maintenance.py
usage: python maintenance.py ACTION
ACTION can be:
    change_email
    add_users
    initdb
    generate
```
