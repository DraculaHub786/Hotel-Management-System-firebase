# SECRET_KEY - EXACT PLACEMENT GUIDE

## 🎯 TWO PLACES WHERE SECRET_KEY GOES

### PLACE #1: Your Local .env File (For Testing)

**File:** `.env` (in your project root, same folder as app.py)

**Current content:**
```
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
HOST=0.0.0.0
PORT=5000
```

**What to change:**
```
FLASK_ENV=development
SECRET_KEY=YOUR_64_CHARACTER_HEX_STRING_HERE  ← REPLACE THIS
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
HOST=0.0.0.0
PORT=5000
```

Example (with real key):
```
FLASK_ENV=development
SECRET_KEY=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
HOST=0.0.0.0
PORT=5000
```

⚠️ **IMPORTANT:** 
- This .env file is in .gitignore (not committed)
- Use for local testing only
- Never share this file

---

### PLACE #2: Render Dashboard (For Production/Cloud)

#### Where to Find It:

1. **Go to render.com**
2. **Click your Web Service** (hotel-management-system)
3. **Left sidebar → Scroll down**
4. **Click "Environment"** 
   - You'll see a form like in your screenshot

#### Exact Steps:

**In the Environment Variables Form:**

1. **First Field (Left side):** Type `SECRET_KEY`
2. **Second Field (Right side):** Paste your 64-character hex string
3. **Optional:** Check the "Secret" checkbox (hides the value)
4. **Click:** "Add Environment Variable" button
5. **Then:** Scroll down and click "Deploy Web Service"

#### Visual Representation:

```
Environment Variables
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  NAME_OF_VARIABLE              | value                      │
│  ┌──────────────────────────┐  │ ┌──────────────────────┐   │
│  │ SECRET_KEY               │  │ │ a1b2c3d4e5f6a1b2c3d │    │
│  │                          │  │ │ 4e5f6a1b2c3d4e5f6a1 │    │
│  │                          │  │ │ b2c3d4e5f6a1b2c3d4e │    │
│  │                          │  │ │ 5f6a1b2c3d4e5f6      │   │
│  └──────────────────────────┘  │ └──────────────────────┘   │
│                                │ ☑️ Secret (check this)     │
│  ☒ Required                   │                            │
│                                │ Generate | Delete         │
│  + Add Environment Variable    │                           │
│  📄 Add from .env              │                           │
│                                │                           │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ COMPLETE CHECKLIST

- [ ] Generate SECRET_KEY (64-char hex string)
- [ ] Add SECRET_KEY to local .env file
- [ ] Test locally: `python app.py`
- [ ] Go to render.com dashboard
- [ ] Click your Web Service
- [ ] Click "Environment" in sidebar
- [ ] Add variable:
  - Name: `SECRET_KEY`
  - Value: [Your 64-char string]
- [ ] Check "Secret" checkbox (optional but recommended)
- [ ] Click "Add Environment Variable"
- [ ] Click "Deploy Web Service"
- [ ] Wait for deployment
- [ ] Test: `curl https://your-app.onrender.com/api/health`

---

## 🔒 SECURITY REMINDERS

✅ **DO:**
- Keep SECRET_KEY secret
- Use different key for each environment (local vs production)
- Regenerate if accidentally exposed
- Use Render's "Secret" checkbox to hide it

❌ **DON'T:**
- Commit SECRET_KEY to git
- Share SECRET_KEY via chat/email
- Use same key in multiple environments
- Post screenshots with SECRET_KEY visible

---

## EXAMPLE: Complete Environment Variables in Render

After adding all 5 variables, your Render dashboard should show:

```
Environment Variables:

FLASK_ENV = production
HOST = 0.0.0.0
PORT = 10000
FIREBASE_CREDENTIALS_PATH = firebase-credentials.json
SECRET_KEY = ••••••••••••••••••••••••••••••••••••••• (Secret - Hidden)
```

---

## VERIFICATION

After deployment, verify SECRET_KEY is working:

1. Go to Render logs
2. Look for: `✅ Using SECRET_KEY from environment`
3. No errors about missing SECRET_KEY
4. App stays running without crashes

If you see: `❌ ERROR: SECRET_KEY must be set in production!`
→ Go back and re-add SECRET_KEY in Environment Variables

---

## NEED HELP?

If SECRET_KEY causes issues after deployment:

**Check 1:** Is it set in Render Environment?
- Dashboard → Environment → Look for SECRET_KEY

**Check 2:** Did you click "Deploy Web Service"?
- After adding variables, must deploy for changes to take effect

**Check 3:** Check Render logs for errors
- Render Dashboard → Logs tab
- Look for SECRET_KEY error messages

**Check 4:** Restart the service
- Click "Restart Service" button in Render dashboard
