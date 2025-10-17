# Deployment Guide - Meeting Prep Assistant on Coolify

## Overview
Deploy the Meeting Prep Assistant to your VPS using Coolify at **meetings.sohiyou.com**

**Server Details:**
- VPS IP: `158.220.81.23`
- Platform: Coolify
- Domain: `sohiyou.com` (via Cloudflare)
- Subdomain: `meetings.sohiyou.com`

---

## Step 1: DNS Configuration in Cloudflare

### Add DNS Record

1. **Log in to Cloudflare Dashboard**
   - Go to: https://dash.cloudflare.com
   - Select domain: `sohiyou.com`

2. **Add A Record**
   - Go to: DNS → Records
   - Click: **Add record**
   - Settings:
     ```
     Type: A
     Name: meetings
     IPv4 address: 158.220.81.23
     Proxy status: Proxied (orange cloud) ✓
     TTL: Auto
     ```
   - Click: **Save**

3. **Verify DNS Propagation** (wait 1-5 minutes)
   ```bash
   nslookup meetings.sohiyou.com
   # Should show: 158.220.81.23 (or Cloudflare proxy IPs)
   ```

---

## Step 2: Push Code to Git Repository

Coolify deploys from Git repositories. You need to push your code to GitHub/GitLab/Gitea.

### Initialize Git (if not already done)

```bash
cd /Users/marclien/Dev/meeting-prep-assistant

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Meeting Prep Assistant"
```

### Push to GitHub

```bash
# Create a new repository on GitHub: https://github.com/new
# Name it: meeting-prep-assistant

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/meeting-prep-assistant.git

# Push code
git branch -M main
git push -u origin main
```

---

## Step 3: Deploy on Coolify

### 3.1 Access Coolify Dashboard

1. Open your browser
2. Go to: `http://158.220.81.23:8000` (or your Coolify URL)
3. Log in to Coolify

### 3.2 Create New Project

1. Click: **+ New** → **Project**
2. Name: `Meeting Prep Assistant`
3. Click: **Create**

### 3.3 Add New Resource

1. Inside the project, click: **+ New Resource**
2. Select: **Public Repository** (if public) or **Private Repository** (if private)
3. Configuration:
   ```
   Repository URL: https://github.com/YOUR_USERNAME/meeting-prep-assistant
   Branch: main
   Build Pack: Dockerfile
   Port: 5001
   ```
4. Click: **Continue**

### 3.4 Configure Application

**General Settings:**
- **Name:** `meeting-prep-assistant`
- **Port:** `5001`
- **Health Check Path:** `/`

**Build Settings:**
- **Build Pack:** Dockerfile
- **Dockerfile Location:** `./Dockerfile`

**Domains:**
- Click: **+ Add Domain**
- Enter: `meetings.sohiyou.com`
- Enable: **HTTPS** (Let's Encrypt)

### 3.5 Set Environment Variables

1. Go to: **Environment Variables** tab
2. Add the following variables:

```env
# Required
VAPI_API_KEY=your_vapi_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional
VAPI_PHONE_NUMBER_ID=your_phone_number_id_here

# Database path (required)
DATABASE_PATH=/app/data/meeting_prep.db

# Flask settings
FLASK_ENV=production
FLASK_DEBUG=0
```

**Important:** Mark `VAPI_API_KEY` and `ANTHROPIC_API_KEY` as **Secret** (click the eye icon)

### 3.6 Configure Persistent Storage

1. Go to: **Storages** tab
2. Click: **+ Add Storage**
3. Add two volumes:

**Volume 1: Database**
```
Name: meeting-data
Source: /app/data
Destination: /app/data
```

**Volume 2: Meeting Notes**
```
Name: meeting-notes
Source: /app/meeting-notes
Destination: /app/meeting-notes
```

### 3.7 Deploy Application

1. Click: **Deploy** button (top right)
2. Wait for build to complete (5-10 minutes first time)
3. Monitor logs in real-time

---

## Step 4: Verify Deployment

### Check Application Status

1. **In Coolify:**
   - Status should show: **Running** (green)
   - Build logs should show: `Successfully built`

2. **Access Application:**
   - Go to: https://meetings.sohiyou.com
   - You should see the Meeting Prep Assistant homepage

3. **Test Health Check:**
   ```bash
   curl -I https://meetings.sohiyou.com
   # Should return: HTTP/2 200
   ```

---

## Step 5: SSL/HTTPS Configuration

Coolify automatically provisions SSL certificates via Let's Encrypt.

**Verify HTTPS:**
1. Open: https://meetings.sohiyou.com
2. Check for 🔒 lock icon in browser
3. Certificate should be valid

**If SSL Fails:**
1. In Coolify, go to: Domains
2. Click: **Renew Certificate**
3. Wait 1-2 minutes
4. Refresh browser

---

## Accessing the Application

**Public URL:** https://meetings.sohiyou.com

**Features Available:**
- ✅ Make new calls from web interface
- ✅ View all past calls
- ✅ Search calls
- ✅ View detailed transcripts and summaries

---

## Viewing Logs

### In Coolify Dashboard

1. Go to your application in Coolify
2. Click: **Logs** tab
3. View real-time logs

### Via Command Line (SSH)

```bash
# SSH into your VPS
ssh root@158.220.81.23

# View container logs
docker logs -f <container_name>

# Find container name
docker ps | grep meeting-prep
```

---

## Troubleshooting

### Application Won't Start

**Check Build Logs:**
1. Coolify → Your App → **Build Logs**
2. Look for errors in Python package installation

**Common Issues:**
```bash
# Issue: Port already in use
# Solution: Change port in Dockerfile and Coolify config

# Issue: Database permission denied
# Solution: Ensure volume permissions are correct
docker exec -it <container> chmod 777 /app/data
```

### Domain Not Accessible

**DNS Issues:**
```bash
# Check DNS propagation
dig meetings.sohiyou.com
nslookup meetings.sohiyou.com

# Wait 5-10 minutes for DNS to propagate
```

**Cloudflare Issues:**
- Ensure proxy is enabled (orange cloud)
- Check SSL/TLS mode: Should be **Full** or **Full (strict)**
- Cloudflare → SSL/TLS → Overview

### Database Issues

**Reset Database:**
```bash
# SSH into VPS
ssh root@158.220.81.23

# Find container
docker ps | grep meeting-prep

# Access container
docker exec -it <container_name> bash

# Remove database
rm /app/data/meeting_prep.db

# Restart container (in Coolify)
```

### Environment Variables Not Loading

1. Coolify → Your App → **Environment Variables**
2. Verify all variables are set
3. Click: **Restart** to reload variables

---

## Updating the Application

### Deploy New Changes

```bash
# Local machine - commit changes
git add .
git commit -m "Update: description of changes"
git push origin main

# Coolify will auto-deploy (if webhook enabled)
# Or manually click: Deploy button in Coolify
```

### Manual Redeploy

1. Coolify → Your App
2. Click: **Redeploy** button
3. Wait for build to complete

---

## Monitoring & Maintenance

### Check Application Health

```bash
# Health check endpoint
curl https://meetings.sohiyou.com/api/stats

# Should return JSON with call statistics
```

### View Database Size

```bash
ssh root@158.220.81.23
docker exec -it <container> ls -lh /app/data/
```

### Backup Database

```bash
# From VPS
docker cp <container>:/app/data/meeting_prep.db ./backup-$(date +%Y%m%d).db

# Download to local machine
scp root@158.220.81.23:./backup-*.db ./
```

---

## Security Checklist

- ✅ Environment variables marked as secrets
- ✅ HTTPS enabled (Let's Encrypt)
- ✅ Cloudflare proxy enabled (DDoS protection)
- ✅ Database stored in persistent volume
- ✅ API keys never committed to Git

---

## Performance Optimization

### Coolify Settings

**Resources:**
- CPU: 1-2 cores recommended
- Memory: 1GB minimum, 2GB recommended

**Scaling:**
- Workers: 2 (in Dockerfile)
- Threads: 4 (in Dockerfile)

**Adjust if needed:**
```dockerfile
# In Dockerfile, line with gunicorn:
--workers 4 --threads 8  # For more traffic
```

---

## Support & Resources

**Coolify Documentation:**
- https://coolify.io/docs

**Troubleshooting:**
- Coolify Discord: https://coolify.io/discord
- GitHub Issues: https://github.com/coollabsio/coolify/issues

**Application Logs:**
- Coolify Dashboard → Logs
- Real-time monitoring available

---

## Quick Reference Commands

```bash
# SSH into VPS
ssh root@158.220.81.23

# View running containers
docker ps

# View logs
docker logs -f <container_name>

# Access container shell
docker exec -it <container_name> bash

# Restart container
docker restart <container_name>

# Check disk usage
df -h
docker system df
```

---

## Success Checklist

- [ ] DNS A record added in Cloudflare
- [ ] Code pushed to Git repository
- [ ] Application created in Coolify
- [ ] Environment variables configured
- [ ] Persistent volumes configured
- [ ] Domain configured: meetings.sohiyou.com
- [ ] HTTPS certificate active
- [ ] Application accessible at https://meetings.sohiyou.com
- [ ] Test call made successfully
- [ ] Logs accessible

**Your application is now live! 🎉**

Access it at: **https://meetings.sohiyou.com**
