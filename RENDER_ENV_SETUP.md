# RENDER.COM - ENVIRONMENT VARIABLES SETUP GUIDE

## Quick Reference: All Environment Variables You Need

| Variable Name | Value | Type | Notes |
|---|---|---|---|
| `FLASK_ENV` | `production` | Text | Production mode |
| `SECRET_KEY` | [Generate random 32-char] | Secret | Flask session security |
| `FIREBASE_CREDENTIALS_PATH` | `firebase-credentials.json` | Text | Path to credentials file |
| `HOST` | `0.0.0.0` | Text | Bind to all interfaces |
| `PORT` | `10000` | Text | Render default port |

---

## Step-by-Step: Setting Environment Variables in Render

### STEP 1: Access Environment Variables Section

1. Go to your Render service dashboard
2. Click on your web service (hotel-management-system)
3. Scroll down to find **"Environment"** section on the left sidebar
4. Click **"Environment"** or look for **"Environment Variables"** section

### STEP 2: Add Each Variable

Click **"+ Add Environment Variable"** for each variable:

#### Variable 1: FLASK_ENV
- **Name:** `FLASK_ENV`
- **Value:** `production`
- Click **Add**

#### Variable 2: HOST
- **Name:** `HOST`
- **Value:** `0.0.0.0`
- Click **Add**

#### Variable 3: PORT
- **Name:** `PORT`
- **Value:** `10000`
- Click **Add**

#### Variable 4: FIREBASE_CREDENTIALS_PATH
- **Name:** `FIREBASE_CREDENTIALS_PATH`
- **Value:** `firebase-credentials.json`
- Click **Add**

#### Variable 5: SECRET_KEY (IMPORTANT!)

**Generate a secure key:**
```bash
# On Windows PowerShell:
-join (1..32 | ForEach-Object { "{0:x}" -f (Get-Random -Maximum 16) }) | % {$_}

# Or use Python:
python -c "import secrets; print(secrets.token_hex(32))"

# Or use online tool: https://generate-random.org/
```

- **Name:** `SECRET_KEY`
- **Value:** [Paste your generated 64-character hex string]
- **IMPORTANT:** Check the "Secret" checkbox (if available) to hide it
- Click **Add**

---

## STEP 3: Upload Firebase Credentials

### Option A: Via Git (RECOMMENDED)

1. Make sure `firebase-credentials.json` is in your project root
2. Remove it from `.gitignore` temporarily
3. Commit and push to GitHub
4. Render will automatically pick it up
5. Add it back to `.gitignore` after

### Option B: Via Render Web Interface

1. In Render dashboard, go to **"Code & Deploys"** tab
2. Look for file upload or "Add files" option
3. Upload `firebase-credentials.json` to project root
4. Make sure it's in the same directory as `app.py`

### Option C: Via Environment Variable (BASE64)

1. Encode credentials as base64:
```bash
# Windows PowerShell:
[Convert]::ToBase64String([System.IO.File]::ReadAllBytes("firebase-credentials.json")) | clip

# macOS/Linux:
cat firebase-credentials.json | base64
```

2. In Render:
   - **Name:** `FIREBASE_CREDENTIALS_BASE64`
   - **Value:** [Paste base64 string]
   - Add a startup script to decode it (more complex)

---

## STEP 4: Deploy

After setting all environment variables:

1. Click **"Deploy"** or go to **"Deploys"** tab
2. Click **"New Deploy"** 
3. Wait for deployment to complete
4. Check logs for any errors

---

## VERIFICATION

After deployment, verify everything is working:

```bash
# Check if app is running:
curl https://your-app.onrender.com/api/health

# Response should be:
{"status": "healthy", "timestamp": "2026-04-03T18:55:21.123456"}
```

---

## TROUBLESHOOTING

### Problem: "Firebase credentials file not found"
**Solution:**
- Make sure `firebase-credentials.json` is in project root
- Verify filename is exactly correct (case-sensitive)
- Check `.gitignore` - it should be there, but file must be uploaded to Render

### Problem: "SECRET_KEY environment variable must be set in production"
**Solution:**
- Make sure `SECRET_KEY` is set in Render Environment Variables
- Check spelling: must be exactly `SECRET_KEY`
- Generate a new value if needed

### Problem: "ModuleNotFoundError: No module named 'requests'"
**Solution:**
- Verify all dependencies are in `requirements.txt`
- Run `pip install -r requirements.txt` locally to test
- Push updated requirements.txt to GitHub

### Problem: "CORS errors when accessing from frontend"
**Solution:**
- Make sure `ALLOWED_ORIGINS` is set correctly
- Or update in app.py: `CORS(app)` allows all origins (for testing)

### Problem: "Port already in use"
**Solution:**
- Port 10000 is Render's default
- Do NOT change PORT to anything else in Render
- Change `app.run()` to use `port` from environment variable

---

## Full Environment Variables List (Quick Copy-Paste)

```
FLASK_ENV=production
HOST=0.0.0.0
PORT=10000
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
SECRET_KEY=[YOUR_32_CHAR_HEX_STRING]
```

---

## Important Notes

⚠️ **Security:**
- Never commit `firebase-credentials.json` to public GitHub
- Use "Secret" checkbox for sensitive variables like `SECRET_KEY`
- Rotate `SECRET_KEY` regularly in production

✅ **Best Practices:**
- Use Render's "Secrets" feature for sensitive data
- Keep `requirements.txt` up to date
- Test locally first: `python app.py`
- Use different SECRET_KEY for each environment

📝 **Firebase Credentials:**
- Download from Firebase Console → Project Settings → Service Accounts
- Keep only one copy in secure location
- Regenerate if accidentally exposed

---

## Getting Help

- Render Docs: https://render.com/docs/environment-variables
- Flask Docs: https://flask.palletsprojects.com/en/3.0.x/config/
- Firebase Admin: https://firebase.google.com/docs/admin/setup
