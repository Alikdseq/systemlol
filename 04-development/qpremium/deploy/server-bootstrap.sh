#!/usr/bin/env bash
# Bootstrap Ubuntu VPS for Q Premium (run once as root).
# Usage: bash server-bootstrap.sh
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "==> System update"
apt-get update -y
apt-get upgrade -y

echo "==> Packages"
apt-get install -y ca-certificates curl gnupg ufw fail2ban unattended-upgrades

echo "==> Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

echo "==> Caddy"
if ! command -v caddy >/dev/null 2>&1; then
  apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    | tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -y
  apt-get install -y caddy
fi
systemctl enable --now caddy

echo "==> Firewall (22/80/443 only)"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status verbose

echo "==> fail2ban"
systemctl enable --now fail2ban

echo "==> App directory"
mkdir -p /opt/qpremium
chmod 750 /opt/qpremium

echo "==> Done. Next: copy project + .env, then run deploy.sh"
