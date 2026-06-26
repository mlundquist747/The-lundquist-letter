# The Lundquist Letter 📰

Your personalized morning newspaper — delivered to mlundquist747@gmail.com every day at 8:00 AM CT.

Covers: Manufacturing · Finance · Technology · Science · World Affairs · Sports  
Teams: Houston Texans · Houston Astros · Texas A&M

---

## Setup Guide

### Step 1 — Clone & install locally

```bash
git clone https://github.com/YOUR_USERNAME/lundquist-letter.git
cd lundquist-letter
pip install -r requirements.txt
```

---

### Step 2 — Get your Anthropic API key

1. Go to https://console.anthropic.com/
2. Create an API key
3. Save it — you'll add it to GitHub Secrets in Step 4

---

### Step 3 — Set up Gmail OAuth credentials

This is a one-time process that authorizes the script to send email from your Gmail account.

**3a. Create a Google Cloud project & enable Gmail API**

1. Go to https://console.cloud.google.com/
2. Create a new project (name it anything, e.g. "Lundquist Letter")
3. Go to **APIs & Services → Library**
4. Search for **Gmail API** and click **Enable**

**3b. Create OAuth credentials**

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name it anything (e.g. "Lundquist Letter")
5. Click **Create**, then **Download JSON**
6. Rename the downloaded file to `client_secret.json` and place it in this project folder

**3c. Configure the OAuth consent screen**

1. Go to **APIs & Services → OAuth consent screen**
2. User type: **External** (or Internal if using Google Workspace)
3. Fill in App name ("Lundquist Letter"), your email, and save
4. Under **Test users**, add mlundquist747@gmail.com
5. Save

**3d. Run the authorization script**

```bash
python get_gmail_credentials.py
```

A browser window will open. Sign in with mlundquist747@gmail.com and grant access.  
The script will print a JSON blob — copy it, you'll need it in the next step.

---

### Step 4 — Add GitHub Secrets

1. Push this repo to GitHub (create a new private repo)
2. Go to your repo → **Settings → Secrets and variables → Actions**
3. Add two secrets:

| Secret Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key from Step 2 |
| `GMAIL_CREDENTIALS_JSON` | The full JSON from Step 3d |

---

### Step 5 — Enable GitHub Actions

1. Go to your repo → **Actions** tab
2. Click **Enable Actions** if prompted
3. The workflow runs automatically every day at 8:00 AM CT

**To test it manually:**
- Go to Actions → "The Lundquist Letter — Daily Briefing" → **Run workflow**

---

## Adjusting delivery time

Edit `.github/workflows/daily_briefing.yml`:

```yaml
- cron: '0 13 * * *'   # 8:00 AM CDT (UTC-5), Mar–Nov
```

For CST (Nov–Mar, UTC-6), change to `'0 14 * * *'`.

Use https://crontab.guru to calculate UTC times.

---

## Customizing your preferences

Edit the `PREFS` dictionary at the top of `send_briefing.py`:

```python
PREFS = {
    "topics":    ["Manufacturing", "Finance", ...],
    "excludes":  ["celebrity gossip", ...],
    "teams":     ["Houston Texans", "Houston Astros", "Texas A&M"],
    "leagues":   ["NFL", "MLB", "NHL", ...],
    ...
}
```

Commit and push — the next morning's briefing will reflect your changes.

---

## File structure

```
lundquist-letter/
├── send_briefing.py          # Main script
├── get_gmail_credentials.py  # One-time OAuth setup
├── requirements.txt          # Python dependencies
├── .gitignore                # Keeps secrets out of git
├── .github/
│   └── workflows/
│       └── daily_briefing.yml  # Cron schedule
└── README.md
```

---

## Troubleshooting

**Email not arriving?**
- Check Actions tab for errors
- Verify both GitHub Secrets are set correctly
- Make sure your Gmail OAuth token hasn't expired (re-run `get_gmail_credentials.py` if so)

**"Quota exceeded" error?**
- The Anthropic API has rate limits; the script uses ~4 calls per run, well within free tier

**Wrong time?**
- GitHub Actions cron uses UTC. CDT = UTC-5, CST = UTC-6. Adjust the cron accordingly.
