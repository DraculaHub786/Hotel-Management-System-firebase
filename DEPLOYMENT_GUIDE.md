# Deployment Guide: Hotel Management System

## 🔒 Security Changes Made

### 1. **Environment Variables Implementation**
- ✅ Created `.env.example` - Template for all environment variables
- ✅ Created `.env` - Local development configuration (auto-ignored by git)
- ✅ Updated `app.py` to load environment variables using `python-dotenv`
- ✅ Firebase credentials path now loaded from `FIREBASE_CREDENTIALS_PATH` env var
- ✅ Secret key can be set via `SECRET_KEY` env var

### 2. **Files Created**
- `.env.example` - Template for env variables (commit this, not `.env`)
- `.env` - Local development variables (DO NOT commit)
- `.gitignore` - Prevents committing sensitive files
- `render.yaml` - Render.com deployment configuration
- `Procfile` - Process file for Render
- `/api/health` endpoint - Health check for monitoring

### 3. **Updated Files**
- `app.py` - Now loads environment variables securely
  - Uses `load_dotenv()` to read `.env` file
  - Firebase credentials path configurable
  - Secret key from env or randomly generated
  - Health check endpoint added
  - Server configuration from env variables

---

## 🚀 Deployment Steps

### **Step 1: Prepare Your Repository**

```bash
# Initialize git (if not already done)
git init

# Stage all files
git add .

# Commit with message
git commit -m "Add deployment configuration and security improvements"

# Create .env file locally (already done)
# Make sure firebase-credentials.json exists locally
```

### **Step 2: Deploy on Render.com (Recommended for Python)**

1. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the hotel management system repo

3. **Configure Service**
   - **Name**: `hotel-management-system`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free (stays up 24/7 with free tier)

4. **Add Environment Variables** (in Render Dashboard)
   - `FLASK_ENV`: `production`
   - `HOST`: `0.0.0.0`
   - `PORT`: `10000` (Render default)
   - `SECRET_KEY`: [Generate a strong key]
   - `FIREBASE_CREDENTIALS_PATH`: `firebase-credentials.json`

5. **Add Firebase Credentials**
   - Option A: Add as environment variable (copy entire JSON as base64)
   - Option B: Create a Python script to create it at startup
   - For now, upload `firebase-credentials.json` via Git

6. **Deploy**
   - Push changes to GitHub
   - Render auto-deploys when main branch changes
   - Check Render dashboard for deployment status

### **Step 3: Deploy on Vercel (Optional - Frontend)**

If you want to serve the frontend separately:

1. Go to https://vercel.com
2. Import project
3. Select Python/Static option
4. Set API backend URL as environment variable

---

## 📋 Environment Variables Reference

### Required Variables
```
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

### Optional Variables (with defaults)
```
FLASK_ENV=production          # or development
SECRET_KEY=your-secret-key    # Auto-generated if not set
PORT=5000                      # Default port
HOST=0.0.0.0                   # Bind to all interfaces
ALLOWED_ORIGINS=               # CORS allowed origins
```

---

## ✅ Testing Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app.onrender.com/api/health

# Test login (should return 401 without credentials)
curl -X POST https://your-app.onrender.com/api/login

# Test booking data fetch (should work if Firebase is connected)
curl https://your-app.onrender.com/api/rooms
```

---

## 🔧 Keep Free Tier Alive

Render's free tier spins down after 15 minutes of inactivity. To keep it alive:

### Option 1: External Monitoring Service
Use a free service like:
- UptimeRobot (https://uptimeMonitor.io)
- Freshping (https://freshping.io)
- Set to ping your `/api/health` endpoint every 5 minutes

### Option 2: Scheduled Task (Python)
Uncomment and configure in `.env`:
```env
KEEP_ALIVE_URL=https://your-app.onrender.com/api/health
```

---

## 🚨 Security Checklist

- [ ] `.env` file is in `.gitignore` (not committed)
- [ ] `firebase-credentials.json` is NOT in git (in .gitignore)
- [ ] All sensitive data loaded from environment variables
- [ ] `SECRET_KEY` is unique for each environment
- [ ] CORS is properly configured for your domain
- [ ] Health check endpoint is working
- [ ] No hardcoded secrets in code

---

## 📝 Important Notes

1. **First Time Setup**
   - Firebase credentials must be provided to Render
   - Check Render logs for any Firebase connection errors

2. **Local Development**
   - Use `.env` file (already created)
   - Flask will use debug mode automatically
   - Hot reload enabled in development

3. **Production**
   - Set `FLASK_ENV=production` in Render dashboard
   - Debug mode automatically disabled
   - Ensure proper logging is set up

4. **Database**
   - Firebase Firestore is used (free tier available)
   - No local database needed
   - Credentials must be valid

---

## 🆘 Troubleshooting

### App fails to start
- Check Render logs for Firebase credentials error
- Verify `firebase-credentials.json` path
- Ensure all required packages in `requirements.txt`

### Cannot connect to Firebase
- Verify credentials file format
- Check Firebase project hasn't been deleted
- Ensure Firebase project quota hasn't exceeded

### Environment variables not loading
- Verify `.env` file exists locally
- Check variable names in code match `.env`
- Restart app after adding env variables

### Deployment keeps failing
- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure start command is correct

---

## 📚 Useful Links

- Render Docs: https://render.com/docs
- Flask Deployment: https://flask.palletsprojects.com/en/2.3.x/deploying/
- Firebase Admin SDK: https://firebase.google.com/docs/database/admin/start
- python-dotenv: https://python-dotenv.readthedocs.io/
