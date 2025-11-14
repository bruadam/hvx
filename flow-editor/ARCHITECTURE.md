# Architecture Overview

## Application Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│                    http://localhost:3000                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Next.js App Router                        │
│                    app/page.tsx                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FlowEditor Component                     │
│                  (Main Application Logic)                    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  State Management                                   │     │
│  │  • nodes (useNodesState)                           │     │
│  │  • edges (useEdgesState)                           │     │
│  │  • selectedNode (useState)                         │     │
│  │  • modals (useState)                               │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Event Handlers                                     │     │
│  │  • onDrop - Add new nodes                          │     │
│  │  • onConnect - Create edges                        │     │
│  │  • onNodeClick - Select nodes                      │     │
│  │  • handleExport - Export JSON                      │     │
│  │  • handleCSVUpload - Attach data                   │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
          │              │              │              │
          ▼              ▼              ▼              ▼
     ┌────────┐    ┌─────────┐   ┌──────────┐   ┌─────────┐
     │ReactFlow│    │ Node    │   │  CSV     │   │  Help   │
     │ Canvas  │    │ Library │   │  Upload  │   │  Modal  │
     └────────┘    └─────────┘   └──────────┘   └─────────┘
          │
          ▼
     ┌────────┐
     │ Custom │
     │  Node  │
     └────────┘

## Component Hierarchy

```
App (page.tsx)
 └── FlowEditor
      ├── ReactFlow (3rd party)
      │    ├── Background
      │    ├── Controls
      │    ├── Panel (Toolbar)
      │    │    ├── Help Button
      │    │    ├── Export Button
      │    │    └── Clear Button
      │    ├── Panel (Node Details)
      │    │    ├── Node Info Display
      │    │    ├── Delete Button
      │    │    ├── CSV Upload Button
      │    │    └── SampleDataGenerator
      │    └── CustomNode (rendered for each node)
      │         ├── Handle (top - target)
      │         ├── Icon + Label
      │         ├── CSV Info Display
      │         └── Handle (bottom - source)
      ├── NodeLibrary
      │    ├── Spatial Entities Section
      │    │    ├── Portfolio Item
      │    │    ├── Building Item
      │    │    ├── Floor Item
      │    │    └── Room Item
      │    └── Sensors Section
      │         ├── Temperature Item
      │         ├── Humidity Item
      │         ├── CO2 Item
      │         ├── Occupancy Item
      │         ├── Light Item
      │         └── Energy Item
      ├── CSVUploadModal
      │    ├── File Input
      │    ├── Preview Table
      │    ├── Error Display
      │    └── Action Buttons
      └── HelpModal
           ├── Hierarchy Guide
           ├── Quick Start
           ├── Node Types Reference
           └── Pro Tips
```

## Data Flow

### Adding a Node
```
1. User drags from NodeLibrary
   ↓
2. onDragStart sets nodeType in dataTransfer
   ↓
3. User drops on canvas
   ↓
4. onDrop creates new node object
   ↓
5. setNodes adds to nodes array
   ↓
6. React Flow renders CustomNode
```

### Connecting Nodes
```
1. User drags from source handle
   ↓
2. User drops on target handle
   ↓
3. onConnect receives connection params
   ↓
4. addEdge creates edge with styling
   ↓
5. setEdges adds to edges array
   ↓
6. React Flow renders animated edge
```

### Uploading CSV
```
1. User clicks sensor node
   ↓
2. onNodeClick sets selectedNode
   ↓
3. Node details panel renders
   ↓
4. User clicks "Upload CSV"
   ↓
5. CSVUploadModal opens
   ↓
6. User selects file
   ↓
7. PapaParse parses CSV
   ↓
8. Preview renders in modal
   ↓
9. User confirms upload
   ↓
10. handleCSVUpload updates node data
    ↓
11. CustomNode shows CSV info
```

### Exporting Graph
```
1. User clicks Export button
   ↓
2. handleExportJSON collects nodes + edges
   ↓
3. Creates JSON structure
   ↓
4. Blob created from JSON string
   ↓
5. Temporary URL created
   ↓
6. Programmatic download triggered
   ↓
7. File saved to downloads folder
```

## State Management

### Node State
```typescript
const [nodes, setNodes, onNodesChange] = useNodesState([])

// Node structure:
{
  id: string,              // "node_0"
  type: "custom",          // Always custom for our nodes
  position: { x, y },      // Canvas position
  data: {
    label: string,         // Display name
    nodeType: NodeType,    // portfolio, building, etc.
    csvData?: any[],       // Parsed CSV rows
    csvFile?: string       // Original filename
  }
}
```

### Edge State
```typescript
const [edges, setEdges, onEdgesChange] = useEdgesState([])

// Edge structure:
{
  id: string,              // Auto-generated
  source: string,          // Source node ID
  target: string,          // Target node ID
  animated: boolean,       // true for our edges
  style: {
    stroke: string,        // Color
    strokeWidth: number    // Width
  }
}
```

### UI State
```typescript
const [selectedNode, setSelectedNode] = useState<Node | null>(null)
const [isCSVModalOpen, setIsCSVModalOpen] = useState(false)
const [isHelpModalOpen, setIsHelpModalOpen] = useState(false)
const [reactFlowInstance, setReactFlowInstance] = useState<any>(null)
```

## Type System

### Core Types
```typescript
// lib/nodeTypes.ts

type NodeType =
  | 'portfolio' | 'building' | 'floor' | 'room'
  | 'temperatureSensor' | 'humiditySensor' | 'co2Sensor'
  | 'occupancySensor' | 'lightSensor' | 'energySensor'

interface NodeConfig {
  type: NodeType
  label: string        // Display name
  color: string        // Hex color
  icon: string         // Lucide icon name
  category: 'spatial' | 'sensor'
}

interface NodeData {
  label: string
  nodeType: NodeType
  csvData?: any[]
  csvFile?: string
}
```

## Styling Architecture

### Tailwind CSS Classes
- Used for all layout and utility styles
- Responsive breakpoints where needed
- Hover states and transitions
- Color utilities

### Inline Styles
- Dynamic colors from NODE_CONFIGS
- Node-specific styling based on type
- Handle colors matching node colors
- Edge styling

### Global Styles
- React Flow base styles imported
- Custom overrides in globals.css
- Font and layout defaults

## File Size & Performance

### Bundle Composition
- Next.js framework: ~100KB
- React Flow: ~80KB
- React: ~40KB
- Tailwind CSS: ~10KB (purged)
- Lucide Icons: ~5KB (tree-shaken)
- PapaParse: ~30KB
- Custom code: ~20KB

**Total**: ~285KB (estimated, gzipped)

### Optimization Techniques
- React.memo on CustomNode
- useCallback for event handlers
- Lazy loading for modals
- Code splitting by Next.js
- Tree-shaking for icons
- CSS purging for Tailwind

## Security Considerations

### CSV Upload
- File type validation (.csv only)
- Client-side parsing (no server)
- No code execution
- Memory limits via browser

### Data Privacy
- All data stays client-side
- No external API calls
- No analytics tracking
- Export to local filesystem only

### XSS Prevention
- React auto-escapes by default
- No dangerouslySetInnerHTML
- Controlled inputs
- TypeScript type safety

## Browser APIs Used

- **File API**: For CSV file reading
- **Blob API**: For JSON export
- **URL.createObjectURL**: For download
- **Drag and Drop API**: For node library
- **LocalStorage**: Not currently used (future)
- **Canvas API**: Via React Flow

## Dependencies Deep Dive

### React Flow (reactflow)
- **Purpose**: Node-based UI framework
- **Version**: 11.11.4
- **Size**: ~80KB
- **Features Used**:
  - Node positioning
  - Edge connections
  - Controls (zoom, pan)
  - Background
  - Handle system
  - Custom node types

### Lucide React
- **Purpose**: Icon library
- **Version**: 0.454.0
- **Size**: ~5KB (tree-shaken)
- **Icons Used**: ~20 different icons
- **Why**: Lightweight, modern, consistent

### PapaParse
- **Purpose**: CSV parsing
- **Version**: 5.4.1
- **Size**: ~30KB
- **Features Used**:
  - Header parsing
  - Preview mode
  - Error handling
  - Type inference

### Tailwind CSS
- **Purpose**: Utility-first styling
- **Version**: 3.4.14
- **Size**: ~10KB (purged)
- **Why**: Fast development, consistent design

## Build Process

### Development
```bash
npm run dev
```
1. Next.js starts dev server
2. TypeScript compilation on-the-fly
3. Hot module replacement (HMR)
4. Fast refresh for React
5. Tailwind JIT compilation

### Production
```bash
npm run build
```
1. TypeScript compilation
2. React optimization
3. Code splitting
4. Minification
5. CSS purging
6. Static optimization
7. Image optimization (if any)

### Output
- `.next/static` - Static assets
- `.next/server` - Server code
- `out/` - Static export (optional)

## Deployment Architecture

### Vercel (Recommended)
```
GitHub Repo
    ↓
Vercel Auto-Deploy
    ↓
Edge Network (CDN)
    ↓
User Browser
```

### Self-Hosted
```
Build Process
    ↓
Docker Container
    ↓
Web Server (nginx)
    ↓
User Browser
```

### Static Hosting
```
npm run build && npm run export
    ↓
Upload to S3/Netlify/GitHub Pages
    ↓
User Browser
```

## Future Scaling Considerations

### Performance
- Virtualization for 1000+ nodes
- Web Workers for CSV parsing
- IndexedDB for large datasets
- Service Worker for offline

### Features
- Backend API for persistence
- Real-time collaboration (WebSockets)
- User authentication (OAuth)
- Cloud storage integration

### Architecture
- State management library (Zustand/Redux)
- API layer (tRPC/GraphQL)
- Database (PostgreSQL/MongoDB)
- Caching layer (Redis)

---

**Document Version**: 1.0
**Last Updated**: November 14, 2024
**Author**: Development Team
