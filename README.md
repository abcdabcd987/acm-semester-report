# acm-semester-report
Website for submitting ACM Class semester report

## Setup

Postfix mail service needed.

```bash
sudo apt install -y p7zip-full dos2unix
pip3 install -e .
FLASK_APP=acm_report flask initdb
```

## Run Web Server

```bash
# debug
FLASK_APP=acm_report FLASK_DEBUG=1 flask run

# production
gunicorn -b 127.0.0.1:5001 --access-logfile - acm_report:app
```

## Maintenance

```bash
FLASK_APP=acm_report flask
```
