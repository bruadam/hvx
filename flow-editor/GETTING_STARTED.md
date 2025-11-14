# Getting Started Checklist

## ✅ Installation & Setup

### 1. Prerequisites Check
- [ ] Node.js 18 or higher installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Terminal/command prompt access
- [ ] Modern web browser (Chrome, Firefox, Safari, Edge)

### 2. Install Dependencies
```bash
cd flow-editor
npm install
```

**Expected output**: "added 446 packages" (takes ~30-60 seconds)

- [ ] No error messages
- [ ] `node_modules/` directory created
- [ ] `package-lock.json` file created

### 3. Start Development Server
```bash
npm run dev
```

**Expected output**:
```
✓ Ready in 3.1s
- Local:    http://localhost:3000
```

- [ ] Server starts without errors
- [ ] Port 3000 is available
- [ ] URL is displayed in terminal

### 4. Open Application
Open http://localhost:3000 in your browser

- [ ] Page loads successfully
- [ ] No console errors (press F12 to check)
- [ ] Canvas with dotted background visible
- [ ] Right panel shows "Component Library"
- [ ] Top left shows "Help", "Export", "Clear" buttons

## ✅ First Use

### 5. Interface Tour
- [ ] **Canvas** (center): Dotted background where nodes go
- [ ] **Library** (right): Purple, blue, green, amber nodes listed
- [ ] **Toolbar** (top-left): Three colored buttons
- [ ] **Controls** (bottom-left): Zoom and pan controls

### 6. Add First Node
- [ ] Drag "Portfolio" from library to canvas
- [ ] Node appears with purple color
- [ ] Node shows briefcase icon
- [ ] Node label reads "Portfolio 1"

### 7. Create First Connection
- [ ] Drag "Building" node to canvas
- [ ] Hover over Portfolio bottom handle (●)
- [ ] Drag to Building top handle (●)
- [ ] Animated blue line appears connecting nodes

### 8. Test Sensor Features
- [ ] Drag "Temperature" sensor to canvas
- [ ] Click on the sensor node
- [ ] Node Details panel appears (top-right)
- [ ] "Upload CSV" button visible
- [ ] "Quick Sample Data" section visible

### 9. Try Sample Data
- [ ] With sensor selected, click "Temperature Data"
- [ ] Node updates to show "100 records"
- [ ] Node shows "sample_temperature_data.csv"
- [ ] Details panel shows record count

### 10. Test Help System
- [ ] Click purple "Help" button
- [ ] Modal appears with guide
- [ ] Hierarchy diagram visible
- [ ] "Got it!" button present
- [ ] Click to close modal

### 11. Test Export
- [ ] Click blue "Export" button
- [ ] File downloads automatically
- [ ] File is named "spatial-entity-graph.json"
- [ ] File contains valid JSON
- [ ] Nodes and edges present in file

### 12. Test Clear
- [ ] Add at least 3 nodes
- [ ] Click red "Clear" button
- [ ] Confirmation dialog appears
- [ ] Click OK
- [ ] All nodes disappear
- [ ] Canvas is empty

## ✅ Basic Workflow

### 13. Create Complete Hierarchy
- [ ] Add Portfolio node
- [ ] Add Building node below it
- [ ] Connect Portfolio → Building
- [ ] Add Floor node
- [ ] Connect Building → Floor
- [ ] Add Room node
- [ ] Connect Floor → Room
- [ ] Add Temperature sensor
- [ ] Connect Room → Sensor

### 14. Add Data to Sensors
- [ ] Select sensor node
- [ ] Click sample data button OR upload CSV
- [ ] Verify data attached (record count visible)
- [ ] Click on node to verify in details panel

### 15. Export and Verify
- [ ] Export the graph
- [ ] Open JSON file
- [ ] Verify all nodes present
- [ ] Verify connections (edges) present
- [ ] Verify CSV data noted in export

## ✅ Features Verification

### 16. Canvas Interaction
- [ ] **Zoom in**: Mouse wheel up
- [ ] **Zoom out**: Mouse wheel down
- [ ] **Pan**: Click and drag background
- [ ] **Move node**: Click and drag node
- [ ] **Select node**: Single click
- [ ] **Deselect**: Click empty space

### 17. Node Operations
- [ ] **Add node**: Drag from library
- [ ] **Delete node**: Select → click trash icon
- [ ] **View details**: Click node
- [ ] **Connect nodes**: Drag handle to handle

### 18. Sensor Operations
- [ ] **Upload CSV**: Select sensor → Upload button
- [ ] **Sample data**: Select sensor → Sample button
- [ ] **View data info**: Check node for file name
- [ ] **Record count**: Visible on node

### 19. All Node Types Tested
- [ ] Portfolio (purple)
- [ ] Building (blue)
- [ ] Floor (green)
- [ ] Room (amber)
- [ ] Temperature sensor (red)
- [ ] Humidity sensor (cyan)
- [ ] CO2 sensor (slate)
- [ ] Occupancy sensor (purple)
- [ ] Light sensor (yellow)
- [ ] Energy sensor (green)

### 20. Color Coding Verified
- [ ] Each node type has unique color
- [ ] Colors match in library and canvas
- [ ] Handles match node colors
- [ ] Icons are distinct and clear

## ✅ Documentation Review

### 21. Files Read
- [ ] README.md - Project overview
- [ ] USAGE_GUIDE.md - Detailed instructions
- [ ] QUICK_REFERENCE.md - Quick lookup
- [ ] DEMO_SCRIPT.md - Step-by-step walkthrough
- [ ] PROJECT_SUMMARY.md - Technical details
- [ ] ARCHITECTURE.md - System design

### 22. Understanding
- [ ] Know how to start the app
- [ ] Know how to add nodes
- [ ] Know how to connect nodes
- [ ] Know how to upload data
- [ ] Know how to export
- [ ] Know where to get help

## ✅ Troubleshooting

### 23. Common Issues Resolved
- [ ] Port 3000 busy? → Stop other services or use different port
- [ ] npm install fails? → Delete node_modules, run again
- [ ] Page won't load? → Check console for errors
- [ ] Can't drag nodes? → Refresh page
- [ ] Connections won't work? → Drag from bottom to top handle
- [ ] CSV won't upload? → Check file extension (.csv)

## ✅ Advanced Features (Optional)

### 24. Custom CSV Upload
- [ ] Create CSV file with headers
- [ ] Add timestamp column
- [ ] Add data column(s)
- [ ] Upload to sensor
- [ ] Verify preview works
- [ ] Confirm upload successful

### 25. Complex Hierarchies
- [ ] Multiple buildings in portfolio
- [ ] Multiple floors per building
- [ ] Multiple rooms per floor
- [ ] Multiple sensors per room
- [ ] Mix of sensor types

### 26. Performance Testing
- [ ] Add 10+ nodes - smooth?
- [ ] Add 25+ nodes - still smooth?
- [ ] Add 50+ nodes - acceptable?
- [ ] Add 100+ nodes - note any slowdown

## ✅ Production Readiness

### 27. Build Test
```bash
npm run build
```
- [ ] Build completes without errors
- [ ] `.next/` directory created
- [ ] No TypeScript errors
- [ ] No ESLint errors

### 28. Production Start
```bash
npm start
```
- [ ] Production server starts
- [ ] App works in production mode
- [ ] Performance is good

## 🎯 You're Ready When...

- [ ] You can add all node types
- [ ] You can create connections
- [ ] You can upload CSV data
- [ ] You can export to JSON
- [ ] You understand the hierarchy
- [ ] You've read the key documentation
- [ ] The app runs without errors
- [ ] You're comfortable with the interface

## 📊 Progress Tracking

**Total Checkboxes**: 84
**Completed**: _____
**Percentage**: _____%

### Scoring
- **0-20%** (0-17): Just getting started - keep going!
- **21-50%** (18-42): Making progress - you're learning!
- **51-80%** (43-67): Almost there - finish strong!
- **81-100%** (68-84): Expert level - you're ready!

## 🚀 Next Steps After Completion

1. **Try the demo script**: Follow DEMO_SCRIPT.md
2. **Build something real**: Model your actual buildings
3. **Customize**: Add your own node types
4. **Integrate**: Connect to your backend
5. **Share**: Show your team
6. **Contribute**: Suggest improvements

## 📚 Additional Resources

- **In-app Help**: Click the purple Help button
- **README**: Comprehensive project documentation
- **USAGE_GUIDE**: Detailed feature walkthrough
- **ARCHITECTURE**: Technical deep dive
- **QUICK_REFERENCE**: Fast lookup card

## 🎓 Learning Path

### Beginner (Day 1)
- Complete sections 1-12
- Read README.md
- Follow DEMO_SCRIPT.md

### Intermediate (Day 2-3)
- Complete sections 13-22
- Build complex hierarchy
- Upload real CSV data

### Advanced (Day 4+)
- Complete sections 23-28
- Customize node types
- Deploy to production

---

**Last Updated**: November 14, 2024
**Version**: 1.0.0
**Estimated Time**: 1-2 hours for complete checklist

**Need Help?** Check the documentation or open an issue!
