# Node3 Agent Monitoring Dashboards

Two beautiful views to monitor your agent network in real-time.

## 🎨 Marketplace View (Default)

**URL:** http://localhost:8888

### Design
- **Card-based grid layout** - Each agent gets a beautiful card
- **Purple/Blue gradient accents** - Matching marketplace branding
- **Animated status badges** - Pulse effects for working agents
- **Visual agent avatars** - Initials-based colored avatars
- **Rich information display** - All details at a glance

### Features
- ✨ **Animated gradient background**
- 🎴 **Agent cards** with:
  - Status badge (Online/Working/Offline)
  - Platform icon (🪟🐧🍎)
  - GPU badge with vendor and memory
  - Location display
  - MAC address
  - Jobs completed
  - SOL earned
  - Full GPU model name
- 🔍 **Search functionality** - Find agents by hostname, GPU
- 🎯 **Smart filters** - All / Online / Working / Offline
- 📱 **Fully responsive** - Works on mobile, tablet, desktop

### Perfect For
- Executive dashboards
- Public-facing status pages
- Visual presentations
- Marketing materials
- Quick overview

---

## 📊 Table View (Alternative)

**URL:** http://localhost:8888/table

### Design
- **Traditional table layout** - Clean, organized rows
- **Apple-style glass morphism** - Subtle, elegant
- **Compact information** - More agents visible at once
- **Sortable columns** - (Future feature)
- **Hover effects** - Smooth interactions

### Features
- 📋 **Detailed table columns**:
  - Status
  - Hostname
  - Platform
  - GPU vendor and model
  - Memory
  - Location
  - MAC address
  - Jobs
  - Earnings
  - Last seen
- 🔄 **Real-time updates** via WebSocket
- 🎨 **Dark/Light theme toggle**
- 🎯 **Filter tabs** - All / Online / Offline

### Perfect For
- System administrators
- Technical monitoring
- Data analysis
- Detailed investigations
- Export-friendly view

---

## 🎯 Which One to Use?

### Use **Marketplace View** when:
- ✅ Presenting to non-technical audiences
- ✅ Showing on public dashboards
- ✅ Marketing your network
- ✅ You want visual impact
- ✅ Mobile viewing is important

### Use **Table View** when:
- ✅ You need to see many agents at once
- ✅ Technical monitoring and debugging
- ✅ Comparing specific metrics
- ✅ Copying data (MAC addresses, IDs)
- ✅ Traditional admin interface preferred

---

## 🚀 Quick Comparison

| Feature | Marketplace View | Table View |
|---------|-----------------|------------|
| **Layout** | Card Grid | Table Rows |
| **Agents Visible** | ~9-12 per screen | ~20+ per screen |
| **Visual Impact** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Information Density** | Medium | High |
| **Mobile Friendly** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Search** | ✅ Full text | ⚠️ Manual |
| **Filters** | Visual chips | Tab buttons |
| **Animations** | Rich | Subtle |
| **Theme** | Purple/Blue | Apple-style |
| **Best For** | Presentations | Operations |

---

## 🎨 Customization

### Change Marketplace Colors

Edit `marketplace_monitor.html`:

```css
:root {
    --accent-purple: #764ba2;  /* Your purple */
    --accent-blue: #667eea;    /* Your blue */
    --success: #10b981;        /* Online color */
    --warning: #f59e0b;        /* Earnings color */
    --error: #ef4444;          /* Offline color */
}
```

### Change Table Theme

Edit `admin_dashboard.html`:

```css
:root {
    --accent: #007AFF;         /* Accent color */
    --success: #30D158;        /* Success color */
}
```

---

## 🔄 Switching Between Views

Users can bookmark both URLs:

- **Marketplace:** http://localhost:8888
- **Table:** http://localhost:8888/table

Or add navigation links:

```html
<a href="/">Marketplace View</a>
<a href="/table">Table View</a>
```

---

## 📸 Screenshots

### Marketplace View
```
┌─────────────────────────────────────────────┐
│ node³ Marketplace           🟢 Live         │
│ Real-time GPU Compute Network               │
├─────────────────────────────────────────────┤
│ [42] [38] [156] [2.4 SOL]                  │
│ Total  Online  Jobs  Earned                 │
├─────────────────────────────────────────────┤
│ [All] [Online] [Working] [Offline] [Search] │
├─────────────────────────────────────────────┤
│ ┌───────┐  ┌───────┐  ┌───────┐           │
│ │  AG   │  │  MG   │  │  WS   │           │
│ │ agent1│  │ myGPU │  │ workst│           │
│ │ 🟢ONL │  │ ⚡WORK│  │ ⚫OFF │           │
│ │ RTX30 │  │ RTX40 │  │ GTX16 │           │
│ │ 💰0.5 │  │ 💰1.2 │  │ 💰0.1 │           │
│ └───────┘  └───────┘  └───────┘           │
└─────────────────────────────────────────────┘
```

### Table View
```
┌─────────────────────────────────────────────┐
│ node³ Agent Monitor                🟢 Live  │
├─────────────────────────────────────────────┤
│ [42] [38] [156] [2.4 SOL]                  │
├─────────────────────────────────────────────┤
│ Status │ Host  │ GPU   │ Loc │ Jobs │ SOL │
│─────────┼───────┼───────┼─────┼──────┼─────│
│ 🟢 ON  │agent1 │RTX3080│ US  │  45  │ 0.5 │
│ ⚡ WORK│myGPU  │RTX4090│ UK  │  89  │ 1.2 │
│ ⚫ OFF │workst │GTX1660│ DE  │  12  │ 0.1 │
└─────────────────────────────────────────────┘
```

---

## 💡 Tips

1. **Bookmark both views** - Use marketplace for demos, table for ops
2. **Use search** - Find specific agents quickly
3. **Watch the pulse** - Working agents have animated badges
4. **Check location** - See your global distribution
5. **Monitor earnings** - Track SOL in real-time

---

## 🆕 Future Enhancements

### Marketplace View
- [ ] Agent detail modal on click
- [ ] Performance charts per agent
- [ ] GPU utilization graphs
- [ ] Earnings timeline
- [ ] World map visualization

### Table View
- [ ] Column sorting
- [ ] CSV export
- [ ] Multi-select actions
- [ ] Bulk operations
- [ ] Advanced filtering

---

**Both dashboards update in real-time via WebSocket!** 🚀

Choose the view that fits your needs, or use both! 🎨📊

