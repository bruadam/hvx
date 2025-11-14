# Spatial Entity & Sensor Flow Editor

A visual node-based editor built with Next.js and React Flow for defining spatial entities (Portfolio, Building, Floor, Room) and sensors with hierarchical relationships.

## Features

- **Visual Node Editor**: Drag-and-drop interface for creating spatial hierarchies
- **Color-Coded Nodes**: Each node type has a unique color and icon for easy identification
- **Spatial Entities**:
  - Portfolio (Purple)
  - Building (Blue)
  - Floor (Green)
  - Room (Amber)

- **Sensor Types**:
  - Temperature Sensor (Red)
  - Humidity Sensor (Cyan)
  - CO2 Sensor (Slate)
  - Occupancy Sensor (Purple)
  - Light Sensor (Yellow)
  - Energy Sensor (Green)

- **CSV Data Upload**: Upload CSV files to sensor nodes to attach data
- **Connection System**: Wire nodes together to define relationships
- **Export Functionality**: Export your graph structure as JSON
- **Interactive Controls**: Zoom, pan, and organize your spatial hierarchy

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or yarn

### Installation

```bash
cd flow-editor
npm install
```

### Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm start
```

## Quick Start with Sample Data

The `dummy_data/` folder contains sample CSV files and a pre-configured portfolio example:

- **Temperature sensors**: 2 files with hourly temperature data
- **Humidity, CO2, Occupancy, Light sensors**: Room 101 environmental data
- **Energy sensor**: Building-level consumption data
- **Sample portfolio JSON**: Complete example structure

To test with sample data:
1. Start the app (`npm run dev`)
2. Add sensor nodes to the canvas
3. Click a sensor and use "Upload CSV"
4. Browse to `dummy_data/` and select a CSV file
5. Or use the "Quick Sample Data" buttons for instant testing

See [dummy_data/README.md](dummy_data/README.md) for details.

## Usage

1. **Add Nodes**: Drag components from the right panel onto the canvas
2. **Connect Nodes**: Click and drag from the bottom handle of one node to the top handle of another
3. **Upload CSV**: Click on a sensor node and use the "Upload CSV" button in the details panel
4. **Export**: Use the "Export" button to download your graph as JSON
5. **Delete**: Select a node and click the trash icon to remove it

## Technology Stack

- **Next.js 15**: React framework with App Router
- **React Flow**: Node-based graph library
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Icon library
- **PapaParse**: CSV parsing

## Project Structure

```
flow-editor/
├── app/
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Main page
├── components/
│   ├── CustomNode.tsx    # Custom node component
│   ├── FlowEditor.tsx    # Main flow editor
│   ├── NodeLibrary.tsx   # Right panel component library
│   └── CSVUploadModal.tsx # CSV upload modal
├── lib/
│   └── nodeTypes.ts      # Node type definitions
└── package.json
```

## Customization

### Adding New Node Types

Edit `lib/nodeTypes.ts` to add new node types:

```typescript
export const NODE_CONFIGS: Record<NodeType, NodeConfig> = {
  // Add your new node type here
  myNewNode: {
    type: 'myNewNode',
    label: 'My New Node',
    color: '#FF5733',
    icon: 'IconName',
    category: 'spatial' // or 'sensor'
  },
  // ...
};
```

### Styling

Customize colors and styles in:
- `app/globals.css` for global styles
- `tailwind.config.js` for Tailwind configuration
- Individual component files for component-specific styles

## License

See parent project license.
