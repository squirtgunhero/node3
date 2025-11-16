# Download Monitoring Guide

Track and analyze Node3 Agent downloads with multiple monitoring solutions.

## Option 1: GitHub API Analytics (Easiest - Free)

GitHub automatically tracks download counts for release assets.

### Python Script (Instant Stats)

Run the included script to get current statistics:

```bash
# Install requests if needed
pip install requests

# Run analytics script
python download_analytics.py
```

**Output Example:**
```
============================================================
📊 NODE3 AGENT DOWNLOAD STATISTICS
============================================================

🌍 Total Downloads: 1,234
📦 Total Releases: 3

🖥️  DOWNLOADS BY PLATFORM
------------------------------------------------------------
  Windows        456 downloads ( 37.0%)
  Linux          389 downloads ( 31.5%)
  Macos          389 downloads ( 31.5%)

🚀 LATEST RELEASE
------------------------------------------------------------
  Version: v1.0.0
  Published: 2024-11-15T20:30:00Z
  Total Downloads: 789
```

### Web Dashboard (Live Monitoring)

Open `download_dashboard.html` in your browser for a beautiful real-time dashboard:

```bash
open download_dashboard.html
```

Features:
- 📊 Real-time download statistics
- 📈 Platform breakdown charts
- 📉 Release history graphs
- 🔄 Auto-refresh every 5 minutes
- 📱 Mobile responsive

### Host the Dashboard

Host on your node3 website:

```html
<!-- Add to your website -->
<iframe src="download_dashboard.html" width="100%" height="800px"></iframe>
```

Or access GitHub's built-in stats:
```
https://tooomm.github.io/github-release-stats/?username=squirtgunhero&repository=node3
```

## Option 2: Google Analytics Integration

Track download button clicks on your website.

### Add to Your Download Page

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>

<!-- Track download clicks -->
<a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos"
   onclick="gtag('event', 'download', {
     'event_category': 'downloads',
     'event_label': 'macos',
     'value': 1
   });">
  Download for macOS
</a>
```

## Option 3: Custom Download Proxy (Advanced)

Host a proxy server that tracks downloads and redirects to GitHub.

### Flask Proxy Example

Create `download_proxy.py`:

```python
from flask import Flask, redirect, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('downloads.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS downloads
                 (timestamp TEXT, platform TEXT, ip TEXT, user_agent TEXT)''')
    conn.commit()
    conn.close()

init_db()

GITHUB_URLS = {
    'macos': 'https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos',
    'linux': 'https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux',
    'windows': 'https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe'
}

@app.route('/download/<platform>')
def download(platform):
    # Log download
    conn = sqlite3.connect('downloads.db')
    c = conn.cursor()
    c.execute("INSERT INTO downloads VALUES (?, ?, ?, ?)",
              (datetime.now().isoformat(), platform, 
               request.remote_addr, request.user_agent.string))
    conn.commit()
    conn.close()
    
    # Redirect to GitHub
    return redirect(GITHUB_URLS.get(platform, GITHUB_URLS['linux']))

@app.route('/stats')
def stats():
    conn = sqlite3.connect('downloads.db')
    c = conn.cursor()
    
    # Get counts by platform
    c.execute("SELECT platform, COUNT(*) FROM downloads GROUP BY platform")
    platform_stats = dict(c.fetchall())
    
    # Get total
    c.execute("SELECT COUNT(*) FROM downloads")
    total = c.fetchone()[0]
    
    conn.close()
    
    return {
        'total_downloads': total,
        'by_platform': platform_stats
    }

if __name__ == '__main__':
    app.run(port=5000)
```

Update your website download links:
```html
<!-- Instead of GitHub direct links -->
<a href="https://yourdomain.com/download/macos">Download for macOS</a>
```

## Option 4: Plausible Analytics (Privacy-Focused)

Privacy-friendly alternative to Google Analytics.

### Setup

1. Sign up at https://plausible.io
2. Add tracking code to your website:

```html
<script defer data-domain="yournode3site.com" src="https://plausible.io/js/script.js"></script>
```

3. Track downloads:

```html
<a href="..." onclick="plausible('Download', {props: {platform: 'macos'}})">
  Download for macOS
</a>
```

## Option 5: Agent Telemetry (Most Accurate)

Track when agents actually start and connect to marketplace.

### Add to agent's main.py:

```python
import requests
import uuid
import platform

def send_telemetry():
    """Send anonymous telemetry on first startup"""
    telemetry_file = Path.home() / '.node3-agent' / 'telemetry_sent'
    
    if not telemetry_file.exists():
        try:
            data = {
                'agent_id': str(uuid.uuid4()),
                'platform': platform.system(),
                'version': VERSION,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            requests.post(
                'https://api.yournode3site.com/telemetry',
                json=data,
                timeout=5
            )
            
            telemetry_file.parent.mkdir(exist_ok=True)
            telemetry_file.touch()
        except Exception as e:
            logger.debug(f"Telemetry failed: {e}")
```

## Comparison

| Method | Pros | Cons | Accuracy |
|--------|------|------|----------|
| **GitHub API** | Free, easy, built-in | Only tracks completed downloads | Medium |
| **Google Analytics** | Detailed, free | Privacy concerns | Low (tracks clicks) |
| **Download Proxy** | Full control, detailed data | Requires server, bandwidth | High |
| **Plausible** | Privacy-friendly, nice UI | Paid ($9/mo) | Low (tracks clicks) |
| **Agent Telemetry** | Most accurate (actual usage) | Requires agent update | Highest |

## Recommended Approach

**Start with GitHub API + Dashboard** (free, instant):
1. Use `download_analytics.py` for command-line stats
2. Host `download_dashboard.html` on your website
3. Check stats daily/weekly

**Then add Google Analytics** (for website analytics):
1. Track download button clicks
2. See user geography, devices
3. Understand user behavior

**Later, add Agent Telemetry** (for actual usage):
1. Track successful installations
2. Monitor active agents
3. See real adoption rates

## Automated Monitoring

### Cron Job (Linux/macOS)

Run analytics script daily:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /path/to/node3agent && python download_analytics.py >> logs/analytics.log 2>&1
```

### GitHub Actions (Automated Reports)

Create `.github/workflows/analytics.yml`:

```yaml
name: Download Analytics Report

on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight
  workflow_dispatch:

jobs:
  analytics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Generate Report
        run: python download_analytics.py
      
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: weekly-analytics
          path: |
            download_stats.json
            download_stats.csv
```

## Visualization Tools

### Grafana Dashboard

If you're using a download proxy with a database:

1. Install Grafana
2. Connect to your SQLite/PostgreSQL database
3. Create visualizations:
   - Downloads over time
   - Platform distribution
   - Geographic distribution
   - Peak download times

### Simple Web Widget

Add to your website:

```html
<div id="download-stats">
  <script>
    fetch('https://api.github.com/repos/squirtgunhero/node3/releases/latest')
      .then(r => r.json())
      .then(data => {
        const total = data.assets.reduce((sum, a) => sum + a.download_count, 0);
        document.getElementById('download-stats').innerHTML = 
          `<p>🎉 ${total.toLocaleString()} downloads and counting!</p>`;
      });
  </script>
</div>
```

## Privacy Considerations

- ✅ GitHub stats are anonymous (no personal data)
- ✅ Use opt-in telemetry with clear disclosure
- ✅ Don't track IP addresses without consent
- ✅ Comply with GDPR/CCPA if applicable
- ✅ Provide opt-out mechanism for agent telemetry

## Get Started

**Quick start (5 minutes):**

```bash
# Get instant stats
python download_analytics.py

# Open dashboard
open download_dashboard.html
```

**Done!** You're now monitoring downloads. 📊

Check the dashboard weekly to track growth and understand which platforms your users prefer!

