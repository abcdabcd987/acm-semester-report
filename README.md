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
python application.py
```

## Add Students

```bash
python maintenance.py add_users
```

## Generate Report

```bash
python maintenance.py generate
```
