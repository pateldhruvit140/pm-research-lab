# PM Research Lab — Cloud Deployment (Render + MongoDB Atlas)

This guide walks you through deploying the full application to the cloud using **Render** (frontend + backend) and **MongoDB Atlas** (database). All services have free tiers.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   MongoDB Atlas     │
│   (Render)      │     │   (Render)      │     │   (Free Cluster)    │
│   Port 3000     │     │   Port 8001     │     │   pm-lab database   │
└─────────────────┘     └─────────────────┘     └─────────────────────┘
    Web Service            Web Service              Cloud Database
```

---

## Step 1: Set Up MongoDB Atlas (Free)

1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) and create a free account
2. Click **"Build a Database"** → Select **M0 Free Tier**
3. Choose a cloud provider and region (pick one closest to you)
4. Set a **database username** and **password** (save these — you'll need them)
5. Under **Network Access**, click **"Add IP Address"** → Select **"Allow Access from Anywhere"** (`0.0.0.0/0`)
6. Go to **"Connect"** → **"Drivers"** → Copy the connection string

Your connection string will look like:
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/pm-lab?retryWrites=true&w=majority
```

Replace `<username>` and `<password>` with the credentials you set in step 4.

---

## Step 2: Deploy Backend on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"+ New"** → **"Web Service"**
3. Connect your **GitHub repo**
4. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `pm-research-backend` |
| **Root Directory** | `backend` |
| **Runtime** | `Docker` |

5. Add **Environment Variables**:

| Key | Value |
|-----|-------|
| `MONGO_URL` | `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/pm-lab?retryWrites=true&w=majority` |
| `DB_NAME` | `pm-lab` |
| `CORS_ORIGINS` | `*` (update to your frontend URL after deploying frontend) |

6. Click **"Create Web Service"**
7. Wait for the build to complete. Note your backend URL (e.g., `https://pm-research-backend.onrender.com`)
8. Verify: open `https://pm-research-backend.onrender.com/api/health` — you should see `{"status": "healthy"}`

---

## Step 3: Deploy Frontend on Render

1. Click **"+ New"** → **"Web Service"**
2. Connect the **same GitHub repo**
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `pm-research-frontend` |
| **Root Directory** | `frontend` |
| **Runtime** | `Docker` |

4. Add **Environment Variable**:

| Key | Value |
|-----|-------|
| `REACT_APP_BACKEND_URL` | `https://pm-research-backend.onrender.com` (your backend URL from Step 2) |

5. Under **Docker** settings, add a **Build Argument**:

| Key | Value |
|-----|-------|
| `REACT_APP_BACKEND_URL` | `https://pm-research-backend.onrender.com` |

> **Important**: `REACT_APP_*` variables must be set as both an environment variable AND a build argument because Create React App bakes them in at build time.

6. Click **"Create Web Service"**
7. Wait for the build to complete. Note your frontend URL (e.g., `https://pm-research-frontend.onrender.com`)

---

## Step 4: Update CORS (Backend)

After both services are deployed, go back to your **backend service** on Render:

1. Go to **Environment** tab
2. Update `CORS_ORIGINS` to your frontend URL:
   ```
   https://pm-research-frontend.onrender.com
   ```
3. Click **"Save Changes"** — the service will redeploy automatically

---

## Step 5: Seed Sample Data

```bash
curl -X POST https://pm-research-backend.onrender.com/api/seed
```

This creates 4 experiments with share codes: `JIT2026A`, `SCF2026B`, `FAD2026C`, `CTL2026D`

---

## Step 6: Verify Everything Works

| Check | URL |
|-------|-----|
| Backend health | `https://pm-research-backend.onrender.com/api/health` |
| Frontend app | `https://pm-research-frontend.onrender.com` |
| Researcher login | `https://pm-research-frontend.onrender.com/researcher/login` (password: `pmresearch2026`) |
| Participant link | `https://pm-research-frontend.onrender.com/study/JIT2026A` |

---

## Render Free Tier Notes

- Free web services **spin down after 15 minutes of inactivity**
- First request after spin-down takes ~30 seconds to cold start
- For a thesis study with real participants, consider upgrading to the **$7/month plan** to keep services always running
- MongoDB Atlas M0 free tier has a 512MB storage limit (more than enough for a thesis study)

---

## Sharing With Participants

Once deployed, your participant links look like:

```
https://pm-research-frontend.onrender.com/study/JIT2026A
```

You can:
- Share this URL directly via email or messaging
- Print the QR code from the researcher dashboard (Experiments page → QR button)
- Post it on flyers or study recruitment materials

---

## Troubleshooting

### Backend shows "Application error"
- Check the **Logs** tab on Render for error details
- Verify `MONGO_URL` is correct and MongoDB Atlas allows access from `0.0.0.0/0`

### Frontend loads but API calls fail
- Verify `REACT_APP_BACKEND_URL` matches your backend URL exactly (no trailing slash)
- Make sure it's set as both environment variable AND build argument
- Check `CORS_ORIGINS` on the backend includes your frontend URL

### MongoDB connection fails
- Go to MongoDB Atlas → Network Access → Ensure `0.0.0.0/0` is listed
- Verify username/password in the connection string
- Make sure the database name in the URL matches `DB_NAME` (`pm-lab`)

### Data not appearing after seed
- Make sure you're hitting the correct backend URL:
  ```bash
  curl -X POST https://pm-research-backend.onrender.com/api/seed
  ```
- Check backend logs on Render for any errors

---

## Summary of All URLs and Credentials

| Item | Value |
|------|-------|
| Frontend | `https://pm-research-frontend.onrender.com` |
| Backend API | `https://pm-research-backend.onrender.com/api` |
| Researcher Password | `pmresearch2026` |
| MongoDB | MongoDB Atlas (your connection string) |
| Database Name | `pm-lab` |
| Share Codes | `JIT2026A`, `SCF2026B`, `FAD2026C`, `CTL2026D` |
