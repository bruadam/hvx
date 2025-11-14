# Quick Reference Card

## 🚀 Getting Started
```bash
cd flow-editor
npm install
npm run dev
```
Open: http://localhost:3000

## 🎨 Node Types & Colors

### Spatial Entities
| Type | Color | Icon | Purpose |
|------|-------|------|---------|
| Portfolio | Purple (#8B5CF6) | 💼 | Top-level organization |
| Building | Blue (#3B82F6) | 🏢 | Individual buildings |
| Floor | Green (#10B981) | 📚 | Floors/levels |
| Room | Amber (#F59E0B) | 🏠 | Individual rooms/spaces |

### Sensors
| Type | Color | Icon | Purpose |
|------|-------|------|---------|
| Temperature | Red (#EF4444) | 🌡️ | Temperature readings |
| Humidity | Cyan (#06B6D4) | 💧 | Humidity measurements |
| CO2 | Slate (#64748B) | 💨 | CO2 levels |
| Occupancy | Purple (#8B5CF6) | 👥 | Occupancy detection |
| Light | Yellow (#FBBF24) | 💡 | Light levels |
| Energy | Green (#22C55E) | ⚡ | Energy consumption |

## ⌨️ Actions

### Canvas Controls
- **Pan**: Click + Drag background
- **Zoom**: Mouse wheel
- **Add Node**: Drag from library
- **Move Node**: Click + Drag node
- **Connect**: Drag bottom handle → top handle
- **Select**: Click node
- **Deselect**: Click background

### Toolbar Buttons
| Button | Action |
|--------|--------|
| 🟣 Help | Open help guide |
| 🔵 Export | Download JSON |
| 🔴 Clear | Delete all nodes |

### Node Actions
- **Click node** → Show details panel
- **Upload CSV** → Attach data to sensor
- **Sample Data** → Quick test data
- **🗑️ Delete** → Remove node

## 📊 CSV Format Examples

### Temperature
```csv
timestamp,temperature,unit
2024-01-01T00:00:00,22.5,Celsius
```

### Humidity
```csv
timestamp,humidity,unit
2024-01-01T00:00:00,45.2,%
```

### CO2
```csv
timestamp,co2,unit
2024-01-01T00:00:00,450,ppm
```

## 🔗 Typical Hierarchy

```
Portfolio
  └─ Building
      └─ Floor
          └─ Room
              └─ Sensor(s)
```

## 💾 Export Structure

```json
{
  "nodes": [
    {
      "id": "node_0",
      "type": "portfolio",
      "label": "Portfolio 1",
      "position": { "x": 100, "y": 50 },
      "csvFile": "data.csv",
      "recordCount": 100
    }
  ],
  "edges": [
    { "source": "node_0", "target": "node_1" }
  ]
}
```

## 🎯 Pro Tips

1. **Start at the top** - Portfolio → Building → Floor → Room
2. **Connect hierarchically** - Parent to child
3. **Use sample data** - Test before uploading real CSV
4. **Export frequently** - Save your work
5. **Color = Type** - Quick visual identification
6. **One sensor per connection** - Keep it simple
7. **Zoom out** - Use fit view to see everything

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| CSV won't upload | Check .csv extension |
| Can't connect nodes | Drag from ● to ● |
| Lost my work | Export JSON regularly |
| Too slow | Reduce nodes (<100) |
| Node disappeared | Check zoom level |

## 📁 File Locations

```
flow-editor/
├── components/     # React components
├── lib/           # Type definitions
├── app/           # Next.js pages
└── node_modules/  # Dependencies
```

## 🔧 Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development |
| `npm run build` | Build for production |
| `npm start` | Start production |
| `npm run lint` | Check code quality |

## 📚 Resources

- **README.md** - Full documentation
- **USAGE_GUIDE.md** - Detailed how-to
- **PROJECT_SUMMARY.md** - Technical overview
- **Help Button** - In-app guide

## 🎨 Color Reference

```
Purple: #8B5CF6
Blue:   #3B82F6
Green:  #10B981
Amber:  #F59E0B
Red:    #EF4444
Cyan:   #06B6D4
Slate:  #64748B
Yellow: #FBBF24
```

## 🌐 URLs

- Development: http://localhost:3000
- Network: Check terminal output

---

**Version**: 1.0.0
**Updated**: November 14, 2024
