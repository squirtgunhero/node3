# Direct Download Links for Website

Use these URLs on your node3 website to let users download the agent directly from GitHub.

## Direct Download URLs

### Always Latest Version (Recommended)

These URLs automatically point to the latest release:

```
macOS:   https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos
Linux:   https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux
Windows: https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe
```

### Specific Version (v1.0.0)

Lock to a specific version:

```
macOS:   https://github.com/squirtgunhero/node3/releases/download/v1.0.0/node3-agent-macos
Linux:   https://github.com/squirtgunhero/node3/releases/download/v1.0.0/node3-agent-linux
Windows: https://github.com/squirtgunhero/node3/releases/download/v1.0.0/node3-agent-windows.exe
```

## Website Integration Examples

### Option 1: Simple HTML Buttons

```html
<!-- Download Section -->
<div class="download-section">
  <h2>Download Node3 Agent</h2>
  <p>Start earning SOL with your GPU</p>
  
  <div class="download-buttons">
    <!-- macOS -->
    <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos" 
       class="download-btn macos"
       download>
      <svg><!-- Apple icon --></svg>
      Download for macOS
    </a>
    
    <!-- Linux -->
    <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux" 
       class="download-btn linux"
       download>
      <svg><!-- Linux icon --></svg>
      Download for Linux
    </a>
    
    <!-- Windows -->
    <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe" 
       class="download-btn windows"
       download>
      <svg><!-- Windows icon --></svg>
      Download for Windows
    </a>
  </div>
</div>
```

### Option 2: Auto-Detect User's Platform

```html
<div class="download-section">
  <h2>Download Node3 Agent</h2>
  <a id="download-btn" href="#" class="download-btn-primary">
    <span id="download-text">Download for Your Platform</span>
  </a>
  <p class="download-subtitle" id="download-subtitle"></p>
  
  <details class="other-platforms">
    <summary>Other platforms</summary>
    <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos">macOS</a>
    <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux">Linux</a>
    <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe">Windows</a>
  </details>
</div>

<script>
// Auto-detect platform
const downloadBtn = document.getElementById('download-btn');
const downloadText = document.getElementById('download-text');
const downloadSubtitle = document.getElementById('download-subtitle');

function detectPlatform() {
  const userAgent = window.navigator.userAgent;
  const platform = window.navigator.platform;
  const macosPlatforms = ['Macintosh', 'MacIntel', 'MacPPC', 'Mac68K'];
  const windowsPlatforms = ['Win32', 'Win64', 'Windows', 'WinCE'];
  const linuxPlatforms = ['Linux x86_64', 'Linux i686'];

  if (macosPlatforms.indexOf(platform) !== -1) {
    return {
      name: 'macOS',
      url: 'https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos',
      icon: '🍎'
    };
  } else if (windowsPlatforms.indexOf(platform) !== -1) {
    return {
      name: 'Windows',
      url: 'https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe',
      icon: '🪟'
    };
  } else if (linuxPlatforms.indexOf(platform) !== -1 || /Linux/.test(platform)) {
    return {
      name: 'Linux',
      url: 'https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux',
      icon: '🐧'
    };
  }
  
  // Default to showing all options
  return null;
}

const platform = detectPlatform();
if (platform) {
  downloadBtn.href = platform.url;
  downloadText.textContent = `${platform.icon} Download for ${platform.name}`;
  downloadSubtitle.textContent = 'Detected automatically';
} else {
  downloadBtn.href = 'https://github.com/squirtgunhero/node3/releases/latest';
  downloadText.textContent = 'Download Node3 Agent';
}
</script>
```

### Option 3: Show Latest Version Number

```html
<div class="download-section">
  <h2>Download Node3 Agent</h2>
  <p class="version">Latest: <span id="latest-version">v1.0.0</span></p>
  
  <div class="download-buttons">
    <!-- Download buttons here -->
  </div>
</div>

<script>
// Fetch latest release info from GitHub API
fetch('https://api.github.com/repos/squirtgunhero/node3/releases/latest')
  .then(response => response.json())
  .then(data => {
    document.getElementById('latest-version').textContent = data.tag_name;
    
    // Optional: Show download count
    const totalDownloads = data.assets.reduce((sum, asset) => 
      sum + asset.download_count, 0
    );
    console.log('Total downloads:', totalDownloads);
  })
  .catch(error => console.error('Error fetching release info:', error));
</script>
```

### Option 4: Full Download Page with Instructions

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Download Node3 Agent</title>
  <style>
    .download-card {
      border: 1px solid #e1e4e8;
      border-radius: 8px;
      padding: 24px;
      margin: 16px 0;
    }
    .download-btn {
      display: inline-block;
      padding: 12px 24px;
      background: #0366d6;
      color: white;
      text-decoration: none;
      border-radius: 6px;
      font-weight: 600;
    }
    .download-btn:hover {
      background: #0256c7;
    }
    .instructions {
      background: #f6f8fa;
      padding: 16px;
      border-radius: 6px;
      margin-top: 16px;
      font-family: monospace;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Download Node3 Agent</h1>
    
    <!-- macOS -->
    <div class="download-card">
      <h3>🍎 macOS (Apple Silicon & Intel)</h3>
      <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos" 
         class="download-btn" download>
        Download for macOS
      </a>
      <div class="instructions">
        # Installation<br>
        curl -L -o node3-agent https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos<br>
        chmod +x node3-agent<br>
        ./node3-agent
      </div>
    </div>
    
    <!-- Linux -->
    <div class="download-card">
      <h3>🐧 Linux (x86_64)</h3>
      <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux" 
         class="download-btn" download>
        Download for Linux
      </a>
      <div class="instructions">
        # Installation<br>
        curl -L -o node3-agent https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux<br>
        chmod +x node3-agent<br>
        ./node3-agent
      </div>
    </div>
    
    <!-- Windows -->
    <div class="download-card">
      <h3>🪟 Windows (x64)</h3>
      <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe" 
         class="download-btn" download>
        Download for Windows
      </a>
      <div class="instructions">
        # Installation (PowerShell)<br>
        Invoke-WebRequest -Uri "https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe" -OutFile "node3-agent.exe"<br>
        .\node3-agent.exe
      </div>
    </div>
    
    <div class="note">
      <h4>System Requirements</h4>
      <ul>
        <li>GPU: NVIDIA, AMD, Apple Silicon, or Intel</li>
        <li>RAM: 4GB minimum, 8GB recommended</li>
        <li>Storage: 1GB free space</li>
        <li>Network: Internet connection</li>
      </ul>
    </div>
  </div>
</body>
</html>
```

## GitHub API for Dynamic Updates

### Get Latest Release Info

```javascript
// Fetch latest release metadata
fetch('https://api.github.com/repos/squirtgunhero/node3/releases/latest')
  .then(response => response.json())
  .then(release => {
    console.log('Version:', release.tag_name);
    console.log('Published:', release.published_at);
    console.log('Downloads:', release.assets.map(a => ({
      name: a.name,
      downloads: a.download_count,
      size: (a.size / 1024 / 1024).toFixed(2) + ' MB'
    })));
  });
```

### Response Example

```json
{
  "tag_name": "v1.0.0",
  "name": "Release v1.0.0",
  "published_at": "2024-11-15T20:30:00Z",
  "assets": [
    {
      "name": "node3-agent-macos",
      "browser_download_url": "https://github.com/squirtgunhero/node3/releases/download/v1.0.0/node3-agent-macos",
      "size": 46137344,
      "download_count": 142
    }
  ]
}
```

## CDN Benefits

GitHub's CDN provides:
- ✅ **Global distribution** - Fast downloads worldwide
- ✅ **High reliability** - 99.9% uptime
- ✅ **Bandwidth** - Unlimited downloads
- ✅ **HTTPS** - Secure downloads
- ✅ **Version control** - Easy rollbacks
- ✅ **Analytics** - Download counts per file

## Update Process

When you release a new version:

1. Create new tag: `./create_release.sh v1.1.0`
2. Links with `/latest/` automatically update
3. Old version links still work: `/download/v1.0.0/...`
4. No changes needed on your website!

## Testing Downloads

Test the links after the build completes:

```bash
# Test macOS download
curl -I https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos

# Should return: HTTP/2 302 (redirect to actual file)
```

## Marketing Tips

On your website, you can add:

1. **Download counter**: Show total downloads using GitHub API
2. **Latest version badge**: Display current version
3. **Platform detection**: Auto-select correct download
4. **Installation videos**: Link to YouTube tutorials
5. **System requirements**: Clear hardware/software needs

## Example: Simple Landing Page

```html
<section class="hero">
  <h1>Start Earning with Your GPU</h1>
  <p>Download Node3 Agent and join the distributed compute network</p>
  
  <a href="https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos" 
     class="cta-button">
    Download Now
  </a>
  
  <p class="download-info">
    Free • Open Source • <span id="version">v1.0.0</span>
  </p>
</section>
```

## Ready to Use!

Once the GitHub Actions build completes (~10-15 minutes), these URLs will work:

- https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos
- https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux
- https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe

Just embed them on your node3 website! 🚀

