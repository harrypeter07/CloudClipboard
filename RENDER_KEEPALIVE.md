# 🔄 Render Service Keep-Alive Guide

## ⚠️ Problem
Render's **free tier** automatically stops services after **15 minutes of inactivity**. This causes the 502 Bad Gateway error when trying to access the site.

## ✅ Solution

I've added a **health check endpoint** (`/health`) to your server. Now you need to:

### Option 1: Use Uptime Monitoring (Recommended)
Use a free uptime monitoring service to ping your server every 5-10 minutes:

1. **UptimeRobot** (Free):
   - Go to https://uptimerobot.com
   - Sign up for free
   - Add a new monitor:
     - Type: HTTP(s)
     - Friendly Name: CloudClipboard Keep-Alive
     - URL: `https://cloudclipboard.onrender.com/health`
     - Monitoring Interval: 5 minutes
   - Save

2. **Cron-Job.org** (Free):
   - Go to https://cron-job.org
   - Sign up for free
   - Create new cron job:
     - URL: `https://cloudclipboard.onrender.com/health`
     - Schedule: Every 5 minutes
   - Save

### Option 2: Update Render Configuration
Update your `render.yaml` to add health checks:

```yaml
services:
  - type: web
    name: cloudclipboard-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: MONGODB_URL
        sync: false
```

### Option 3: Upgrade to Paid Plan
Render's paid plans ($7/month) keep services always running without going to sleep.

## 🔍 How to Check Status

1. **Test Health Endpoint**: Visit `https://cloudclipboard.onrender.com/health`
   - Should return: `{"status": "healthy", "timestamp": "...", "service": "CloudClipboard API"}`

2. **Check Render Dashboard**:
   - Go to https://dashboard.render.com
   - Check service status
   - View logs for any errors

## 📊 Current Status

- ✅ Health check endpoint added: `/health`
- ✅ Web dashboard route: `/` 
- ✅ All API endpoints working
- ⚠️ Need uptime monitoring to keep service active

## 🎯 Quick Fix Right Now

1. Visit: `https://cloudclipboard.onrender.com/health`
2. This will wake up your service
3. Then visit: `https://cloudclipboard.onrender.com/`
4. Set up UptimeRobot to keep it alive permanently

## 💡 Pro Tips

- **Test locally first**: Run `python server/main.py` to test
- **Check Render logs**: Dashboard → Your Service → Logs
- **Health check responds in ~100ms**: Very fast
- **Free tier limitations**: Service sleeps after 15 minutes of no requests
- **Uptime monitoring**: Pings every 5 minutes = no sleep

## 🔧 Troubleshooting

If 502 error persists:
1. Check Render dashboard for service status
2. View logs for error messages
3. Make sure MongoDB URL is set in environment variables
4. Test `/health` endpoint first
5. Check if web dashboard route works after health check

---

**Created**: 2024-12-27  
**Purpose**: Keep CloudClipboard Render service always active  
**Solution**: Health check endpoint + uptime monitoring

