# AWS EC2 Provisioning & SSL Setup Guide

This guide walks you through setting up a free `t2.micro` (or `t3.micro`) EC2 instance, configuring free dynamic DNS with **DuckDNS**, and setting up free SSL certificates with **Let's Encrypt (Certbot)**.

---

## Step 1: Provision the AWS EC2 Instance

1. **Log in to the AWS Console** and navigate to the **EC2 Dashboard**.
2. Click **"Launch Instance"**:
   - **Name**: `converge-ai-assistant`
   - **OS (AMI)**: `Ubuntu Server 24.04 LTS` (64-bit x86) - *Free Tier Eligible*
   - **Instance Type**: `t2.micro` (or `t3.micro` depending on region eligibility) - *Free Tier Eligible*
   - **Key Pair**: Create a new key pair (e.g. `converge-key.pem`). Save this file securely on your computer.
3. **Configure Security Group**:
   - Check **"Allow SSH traffic from: My IP"** (for security, restrict SSH to your local IP).
   - Check **"Allow HTTPS traffic from the internet"** (opens port 443).
   - Check **"Allow HTTP traffic from the internet"** (opens port 80).
4. Launch the instance.

---

## Step 2: Assign an Elastic IP (Static IP)

By default, EC2 public IPs change whenever the instance is restarted. To avoid breaking our webhooks, we need a static IP:

1. In the EC2 Sidebar, under **Network & Security**, click **Elastic IPs**.
2. Click **Allocate Elastic IP address**, select default settings, and click **Allocate**.
3. Select the newly allocated Elastic IP, click **Actions** -> **Associate Elastic IP address**.
4. Choose your running EC2 instance and click **Associate**.
5. Note the Elastic IP address (e.g. `54.210.15.30`).

---

## Step 3: Configure Free Domain (DuckDNS)

1. Go to [DuckDNS](https://www.duckdns.org/) and log in.
2. Under **Domains**, choose a subdomain name (e.g. `my-converge-bot`) and click **add domain**.
3. Your full domain will be: `my-converge-bot.duckdns.org`
4. In the IP address box, paste your EC2 **Elastic IP address** and click **update IP**.

---

## Step 4: Install Docker on the EC2 Host

Connect to your EC2 instance via SSH:
```bash
chmod 400 converge-key.pem
ssh -i converge-key.pem ubuntu@YOUR_ELASTIC_IP
```

Once logged in, run the official Docker installation commands:
```bash
# Update package database
sudo apt update && sudo apt upgrade -y

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add ubuntu user to Docker group (allows running docker without sudo)
sudo usermod -aG docker $USER
```
*Note: Log out and log back in for the group permissions to take effect:*
```bash
exit
ssh -i converge-key.pem ubuntu@YOUR_ELASTIC_IP
```

---

## Step 5: Bootstrap Let's Encrypt SSL Certificates

Nginx will fail to start if it references SSL certificates that do not exist yet. We will bootstrap the SSL process using the HTTP challenge on port 80.

### 1. Create a Temporary Nginx Configuration
Create a temporary local config to handle port 80 requests:
```bash
mkdir -p nginx
cat << 'EOF' > nginx/nginx.conf
events { worker_connections 1024; }
http {
    server {
        listen 80;
        server_name YOUR_SUBDOMAIN.duckdns.org;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 200 'Bootstrapping SSL... Please run certbot now.';
            add_header Content-Type text/plain;
        }
    }
}
EOF
```
*Replace `YOUR_SUBDOMAIN.duckdns.org` with your actual DuckDNS domain.*

### 2. Run Nginx to handle the Port 80 challenge
Create the empty folders and spin up Nginx:
```bash
sudo mkdir -p /etc/letsencrypt
sudo mkdir -p /var/www/certbot
docker compose up -d nginx
```

### 3. Generate Certificates using Certbot
Run Certbot in a temporary Docker container to request the certificate:
```bash
docker run --rm -it \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d YOUR_SUBDOMAIN.duckdns.org \
  --email YOUR_EMAIL@example.com \
  --agree-tos \
  --no-eff-email
```
*Replace `YOUR_SUBDOMAIN.duckdns.org` and `YOUR_EMAIL@example.com`.*

If successful, the certificate files will be generated under `/etc/letsencrypt/live/YOUR_SUBDOMAIN.duckdns.org/`.

### 4. Apply the Production Nginx Configuration
Stop Nginx:
```bash
docker compose down
```

Restore the production Nginx config in `nginx/nginx.conf` (ensure you replace `YOUR_DOMAIN_HERE` with `YOUR_SUBDOMAIN.duckdns.org` in the file).

Then run:
```bash
docker compose up -d --build
```
Nginx will now start successfully on port 80 and 443 with valid SSL certificates!

---

## Step 6: Automating SSL Renewal

Let's Encrypt certificates are valid for 90 days. We can configure a cron job to automatically renew them.

On your EC2 host, open the crontab editor:
```bash
crontab -e
```

Add the following line at the bottom of the file (renews the certificates daily at 3 AM and reloads Nginx):
```cron
0 3 * * * docker run --rm -v /etc/letsencrypt:/etc/letsencrypt -v /var/www/certbot:/var/www/certbot certbot/certbot renew --webroot --webroot-path=/var/www/certbot && docker exec nginx-reverse-proxy nginx -s reload
```
Save and exit. Your SSL certificates are now fully automated and will never expire!
