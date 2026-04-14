# Deploy Papers Scraper on Raspberry Pi 5

This is a step by step guide to host the tool on your Pi so it runs 24/7 on your home network and is accessible from anywhere.

---

## What you need

- Raspberry Pi 5 running Raspberry Pi OS (64-bit recommended)
- Pi connected to your router via ethernet or wifi
- A computer on the same network to SSH into the Pi
- Your GitHub repo URL

---

## Step 1 - Find your Pi's local IP

On the Pi or from your router admin page, find the Pi's local IP. It looks like `192.168.1.xxx`.

You can also run this on the Pi:

```bash
hostname -I
```

Write it down, you'll need it.

---

## Step 2 - SSH into the Pi

From your computer:

```bash
ssh pi@192.168.1.xxx
```

Default username is `pi`, default password is `raspberry` unless you changed it during setup.

---

## Step 3 - Update the system

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Step 4 - Install dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Step 5 - Clone your repo

```bash
cd ~
git clone https://github.com/b-elamine/papers-scraper.git
cd papers-scraper
```

---

## Step 6 - Set up the Python environment

```bash
bash setup.sh
```

This creates the `.venv` and installs everything from `requirements.txt`.

---

## Step 7 - Test it manually

Before setting up the service, make sure it runs:

```bash
source .venv/bin/activate
gunicorn app:app --worker-class gevent --workers 2 --timeout 120 --bind 0.0.0.0:5000
```

Open a browser on your computer and go to:

```
http://192.168.1.xxx:5000
```

If you see the interface, everything works. Stop gunicorn with `Ctrl+C` and move on.

---

## Step 8 - Create a systemd service

This makes the app start automatically when the Pi boots and restart if it crashes.

Create the service file:

```bash
sudo nano /etc/systemd/system/papers-scraper.service
```

Paste this in (replace `pi` with your username if different):

```ini
[Unit]
Description=Papers Scraper
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/papers-scraper
Environment="PATH=/home/pi/papers-scraper/.venv/bin"
ExecStart=/home/pi/papers-scraper/.venv/bin/gunicorn app:app --worker-class gevent --workers 2 --timeout 120 --bind 0.0.0.0:5000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save and exit: `Ctrl+X` then `Y` then `Enter`.

---

## Step 9 - Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable papers-scraper
sudo systemctl start papers-scraper
```

Check it's running:

```bash
sudo systemctl status papers-scraper
```

You should see `active (running)`. The app is now live at `http://192.168.1.xxx:5000` and will survive reboots.

---

## Step 10 - Access it from outside your home network

Right now the tool is only accessible on your local network. To reach it from anywhere:

### Option A - DuckDNS (free dynamic DNS)

Your home IP changes occasionally. DuckDNS gives you a fixed URL like `yourname.duckdns.org` that always points to your home.

1. Go to `https://www.duckdns.org` and sign in
2. Create a subdomain, e.g. `papers-scraper.duckdns.org`
3. Install the DuckDNS update script on the Pi so it keeps the IP updated:

```bash
mkdir -p ~/duckdns
nano ~/duckdns/duck.sh
```

Paste this (replace `yourtoken` and `yoursubdomain`):

```bash
echo url="https://www.duckdns.org/update?domains=yoursubdomain&token=yourtoken&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

Make it executable and add a cron job to run it every 5 minutes:

```bash
chmod +x ~/duckdns/duck.sh
crontab -e
```

Add this line at the bottom:

```
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

### Option B - Port forwarding on your router

1. Log into your router admin page (usually `192.168.1.1`)
2. Find the port forwarding section
3. Add a rule: external port `5000` -> Pi's local IP -> internal port `5000`
4. Save

After this, your tool is accessible at `http://yourname.duckdns.org:5000` from anywhere in the world.

---

## Useful commands

Check if the service is running:
```bash
sudo systemctl status papers-scraper
```

See live logs:
```bash
sudo journalctl -u papers-scraper -f
```

Restart the service:
```bash
sudo systemctl restart papers-scraper
```

Stop the service:
```bash
sudo systemctl stop papers-scraper
```

---

## Update the app when you push new code

SSH into the Pi and run:

```bash
cd ~/papers-scraper
git pull
sudo systemctl restart papers-scraper
```

That's it.
