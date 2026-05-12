# FRDB deployment (Linux + Nginx + Certbot)

These instructions assume the `frdb` user already exists, the code is installed
at `/home/frdb/frdb`, and the site is served as `frdb.qclub.au`. Adjust paths
or domain names before copying the files if your server uses different values.

## 1) System packages

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip nginx certbot python3-certbot-nginx
```

## 2) App install

Clone the repository as the `frdb` user:

```bash
sudo -u frdb -H bash -lc "git clone <repo_url> /home/frdb/frdb"
```

Create the virtual environment and install the production dependencies:

```bash
sudo -u frdb -H bash -lc "cd /home/frdb/frdb \
  && python3 -m venv .venv \
  && . .venv/bin/activate \
  && pip install --upgrade pip \
  && pip install -r deploy/requirements.txt"
```

Ensure the upload directory exists and is owned by the app user:

```bash
sudo -u frdb -H bash -lc "mkdir -p /home/frdb/frdb/uploads"
```

## 3) Application settings

FRDB sends verification codes for contact and proposal forms through Amazon SES
using the SES SMTP endpoint in `ap-southeast-2`. The host, port, STARTTLS
setting, and timeout defaults live in `frdb/mail/config.py`.

The deployment uses `/home/frdb/frdb/local_settings.py` as the required source
of truth for secret mail settings. It is intentionally ignored by git.

```bash
sudo -u frdb -H cp /home/frdb/frdb/local_settings.example.py /home/frdb/frdb/local_settings.py
sudo chmod 0600 /home/frdb/frdb/local_settings.py
sudo -u frdb -H "${EDITOR:-nano}" /home/frdb/frdb/local_settings.py
```

Set `MAIL_CONFIG.username` and `MAIL_CONFIG.password` to the SES SMTP
credentials, and set `MAIL_CONFIG.sender` to a verified SES sender.

Before deploying, verify that the settings file imports and can send mail:

```bash
cd /home/frdb/frdb
.venv/bin/python script/send_test_email.py you@example.com
```

For the full local verification flow with real emails, run the app with those
same settings, open `http://127.0.0.1:5000/contact-us`, and use the code
delivered to your inbox.

## 4) systemd service

Copy the service file and enable it:

```bash
sudo cp /home/frdb/frdb/deploy/frdb.service /etc/systemd/system/frdb.service
sudo systemctl daemon-reload
sudo systemctl enable --now frdb.service
sudo systemctl status frdb.service
```

The service runs as `frdb:frdb`, imports `/home/frdb/frdb/local_settings.py`,
and binds Gunicorn to `/home/frdb/frdb.sock`. This matches the simple socket
pattern used by the other small services on the server.

## 5) Nginx configuration

Copy the Nginx config and enable it:

```bash
sudo cp /home/frdb/frdb/deploy/nginx.conf /etc/nginx/sites-available/frdb
sudo ln -s /etc/nginx/sites-available/frdb /etc/nginx/sites-enabled/frdb
sudo nginx -t
sudo systemctl reload nginx
```

The config proxies requests to the Gunicorn Unix socket; Flask serves the app
routes and static assets from the `frdb` checkout.

## 6) TLS certificates with Certbot

The included Nginx config uses the same `/etc/letsencrypt/live/qclub.au`
certificate paths as the other `qclub.au` services. If this certificate already
covers `frdb.qclub.au`, reload Nginx after enabling the site.

If you need to issue or expand the certificate, run:

```bash
sudo certbot --nginx -d frdb.qclub.au
sudo systemctl reload nginx
```

## 7) Verifying

```bash
curl -I https://frdb.qclub.au/
curl https://frdb.qclub.au/api/research-data
```

The API response should contain non-empty `rows` and `filters`.

## 8) Updating the deployment

After the initial setup, deploy updates with:

```bash
cd /home/frdb/frdb
FRDB_BASE_URL=https://frdb.qclub.au deploy/deploy.sh
```

The script pulls the latest code, updates the virtual environment, restarts
`frdb` and Nginx, then verifies the home page and research-data API.
