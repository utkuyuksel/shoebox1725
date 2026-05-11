# VPS Deploy Guide

This is the first-time setup on a fresh Ubuntu VPS plus the day-to-day
deploy loop. We self-host everything in docker-compose on a single box
because the founder already owns a VPS — no Fly.io, no Neon, no Upstash.

## 0. What you need before starting

| Item | Why |
|---|---|
| Ubuntu 22.04 LTS or newer VPS, ≥ 2 GB RAM, ≥ 20 GB disk | Enough for the four containers + 6 months of api-sports data |
| SSH access as a non-root user with sudo | Docker root socket is sensitive |
| A domain you control (e.g. `shoebox.app`) | For SSL + a clean API URL |
| DNS A record `api.shoebox.app` → VPS IP | Let's Encrypt verifies via DNS |
| Ports 80 + 443 open on the firewall | HTTP + HTTPS |

## 1. Prepare the VPS (one-time, ~10 min)

SSH into the box as your user.

```bash
# System update
sudo apt update && sudo apt upgrade -y

# Docker engine + compose plugin
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Let your user run docker without sudo
sudo usermod -aG docker $USER
newgrp docker   # or log out + back in

# Verify
docker --version && docker compose version

# Firewall — only SSH + HTTP + HTTPS exposed
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 2. Pull the repo

```bash
sudo mkdir -p /opt/shoebox && sudo chown $USER:$USER /opt/shoebox
cd /opt
git clone https://github.com/utkuyuksel/shoebox1725.git shoebox
cd shoebox
```

Replace the GitHub URL above with your actual repo path. If the repo is
private, set up a deploy key (SSH) on this VPS first.

## 3. Configure secrets

```bash
cd /opt/shoebox/infra
cp .env.example .env
nano .env
```

Fill in:
* `POSTGRES_PASSWORD` — generate with `openssl rand -base64 32`
* `APISPORTS_KEY` — from your api-sports.io dashboard
* `SUPABASE_URL` — `https://YOUR_PROJECT.supabase.co`
* `REVENUECAT_SECRET_API_KEY` — RC dashboard → API Keys → secret key
* `PUBLIC_BASE_URL` — `https://api.shoebox.app` (your real domain)
* Everything else — leave empty or default until you actually use them

Lock down the file:

```bash
chmod 600 /opt/shoebox/infra/.env
```

## 4. Issue the first SSL certificate

Nginx needs the cert files to start, and certbot needs nginx to serve the
ACME challenge — a chicken-and-egg loop. We resolve it with a one-shot
standalone request before bringing the stack up.

```bash
cd /opt/shoebox/infra
mkdir -p nginx/letsencrypt nginx/certbot-www

# Edit the domain in nginx/conf.d/shoebox.conf — replace every occurrence
# of `api.shoebox.app` with your real domain. Use sed or your editor.
sed -i 's/api.shoebox.app/api.YOUR_DOMAIN/g' nginx/conf.d/shoebox.conf

# Run certbot once in standalone mode (port 80 must be free)
docker run --rm -it \
    -p 80:80 \
    -v $(pwd)/nginx/letsencrypt:/etc/letsencrypt \
    -v $(pwd)/nginx/certbot-www:/var/www/certbot \
    certbot/certbot certonly --standalone \
    --email you@example.com --agree-tos --no-eff-email \
    -d api.YOUR_DOMAIN
```

When this succeeds the cert + key live in
`infra/nginx/letsencrypt/live/api.YOUR_DOMAIN/`.

## 5. Bring up the stack

```bash
cd /opt/shoebox/infra
docker compose -f docker-compose.prod.yml up -d
```

Check it's healthy:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs api --tail 50
curl -sS https://api.YOUR_DOMAIN/
```

Expected: `{"status":"ok","service":"Shoebox API","version":"0.2.0"}`

## 6. Run the initial data backfill

Same scripts you ran locally, just inside the running container.

```bash
docker exec -it shoebox-api python -m app.scripts.seed_leagues
docker exec -it shoebox-api python -m app.scripts.backfill_season \
    --all-football --season 2024 --skip-stats
docker exec -it shoebox-api python -m app.scripts.backfill_basketball_season \
    --league 12 --season 2024 --skip-stats
```

(Per-fixture stats requires the api-sports Pro/Ultra plan — kick those off
after the upgrade.)

## 7. Point the mobile app at production

In `mobile/lib/app/env.dart` the default `apiBaseUrl` is `127.0.0.1:8000`
for the dev workflow. Override at build time:

```bash
flutter build ios --release --dart-define=API_BASE_URL=https://api.YOUR_DOMAIN
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.YOUR_DOMAIN
```

Or set a permanent prod default by editing `env.dart` — pick whichever
matches your deploy hygiene.

## Day-to-day: deploy a code change

After a `git push` from your laptop:

```bash
# On the VPS
cd /opt/shoebox
./infra/deploy.sh
```

The script:
1. `git pull --ff-only`
2. Rebuilds only the API image
3. Recreates the API container (postgres + redis untouched, no data loss)
4. Tails the health endpoint and exits 1 if it never goes green

## Common things you'll want to do

**Tail logs:**
```bash
docker compose -f /opt/shoebox/infra/docker-compose.prod.yml logs -f api
```

**Restart everything:**
```bash
cd /opt/shoebox/infra
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

**Database backup:**
```bash
docker exec shoebox-postgres pg_dump -U postgres shoebox_db | gzip > shoebox-$(date +%F).sql.gz
```

Put the above into `/etc/cron.daily/shoebox-backup` and you have nightly
backups. Upload to S3 / Backblaze / wherever you keep secrets.

**Open the DB:**
```bash
docker exec -it shoebox-postgres psql -U postgres -d shoebox_db
```

**Flush Redis:**
```bash
docker exec shoebox-redis redis-cli FLUSHDB
```

**Update certbot's renewal email or domains:**
The certbot container auto-renews every 12 h. To swap email/domains rerun
step 4 with new flags.

## Resource sizing

The whole stack on idle:

| Service | RAM | Disk (steady state) |
|---|---|---|
| nginx | ~10 MB | tiny |
| api | ~120 MB per worker × 2 workers = ~240 MB | image + logs |
| postgres | ~80 MB | depends on data; a full backfill is ~500 MB after 1 year |
| redis | capped at 256 MB by config | tiny (AOF append-only) |
| certbot | ~30 MB while running, idle otherwise | tiny |

A 2 GB / 1 vCPU VPS handles a few thousand daily active users without
breaking a sweat. Postgres is usually the first bottleneck — upgrade
disk + RAM before CPU.

## Gotchas

* **`docker compose pull` on a new dev branch** — won't rebuild the API
  image (you didn't push to a registry). Use `deploy.sh` or
  `docker compose ... build api` instead.
* **First certbot request fails with "port 80 in use"** — something else
  on the host is listening on 80. Stop it or ssh-tunnel certbot through
  a temporary port (see certbot --http-01-port flag).
* **API can't reach Postgres** — almost always `.env` typo or wrong
  `DATABASE_URL` override in `docker-compose.prod.yml`. Inside the network
  the host is `postgres`, the port is `5432` (not `5433` like dev).
* **Apple's App Transport Security** — iOS will refuse plain HTTP. Make
  sure the cert is valid before pointing the app at production; the mobile
  app's release build won't fall back to HTTP under any circumstances.
* **api-sports rate limits** — backfill scripts honour the per-call sleep
  but the production cron will eventually need its own throttle if we
  ever poll live games. Track `quota_remaining` from the client.
