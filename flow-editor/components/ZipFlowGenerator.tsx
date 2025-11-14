'use client';

import React, { useState } from 'react';
import * as Icons from 'lucide-react';
import Papa from 'papaparse';
import { Node, Edge } from 'reactflow';
import { NodeData, SpatialEntityType, SensorType, MetricType, METRIC_TYPE_INFO } from '@/lib/nodeTypes';

interface ZipFlowGeneratorProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (nodes: Node<NodeData>[], edges: Edge[]) => void;
}

interface ParsedFile {
  name: string;
  content: any[];
  type: 'csv' | 'json';
}

export default function ZipFlowGenerator({
  isOpen,
  onClose,
  onGenerate,
}: ZipFlowGeneratorProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState('');

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.zip')) {
      setError('Please upload a .zip file');
      return;
    }

    setIsProcessing(true);
    setProgress('Reading zip file...');
    setError('');

    try {
      // Dynamically import JSZip
      const JSZip = (await import('jszip')).default;
      const zip = new JSZip();
      const zipContent = await zip.loadAsync(file);

      setProgress('Parsing files...');

      const files: ParsedFile[] = [];

      // Extract all CSV and JSON files
      for (const [filename, fileData] of Object.entries(zipContent.files)) {
        // Skip directories and hidden files
        if (fileData.dir || filename.startsWith('.') || filename.startsWith('__MACOSX')) continue;

        try {
          if (filename.endsWith('.csv')) {
            const content = await fileData.async('text');
            const parsed = Papa.parse(content, { header: true, skipEmptyLines: true });
            if (parsed.data && parsed.data.length > 0) {
              files.push({ name: filename, content: parsed.data, type: 'csv' });
            }
          } else if (filename.endsWith('.json')) {
            const content = await fileData.async('text');
            if (content.trim()) {
              const parsed = JSON.parse(content);
              files.push({ name: filename, content: parsed, type: 'json' });
            }
          }
        } catch (err) {
          console.warn(`Failed to parse ${filename}:`, err);
          // Continue with other files
        }
      }

      if (files.length === 0) {
        throw new Error('No valid CSV or JSON files found in zip');
      }

      setProgress('Generating flow...');

      // Generate nodes and edges from files
      const { nodes, edges } = await generateFlowFromFiles(files);

      setProgress('Flow generated successfully!');

      setTimeout(() => {
        onGenerate(nodes, edges);
        onClose();
        setIsProcessing(false);
        setProgress('');
      }, 500);

    } catch (err: any) {
      console.error('Zip processing error:', err);
      setError(`Error processing zip file: ${err.message || 'Unknown error'}. Please ensure the zip contains valid CSV files.`);
      setIsProcessing(false);
      setProgress('');
    }
  };

  const generateFlowFromFiles = async (files: ParsedFile[]): Promise<{ nodes: Node<NodeData>[], edges: Edge[] }> => {
    const nodes: Node<NodeData>[] = [];
    const edges: Edge[] = [];

    let nodeIdCounter = 0;
    const getId = () => `node_${nodeIdCounter++}`;

    // Parse structure from filenames and create hierarchy
    const spatialEntities = new Map<string, { id: string; type: SpatialEntityType; name: string; parent?: string }>();
    const sensors = new Map<string, { id: string; sensorType: SensorType; fileName: string; csvData: any[] }>();

    // First pass: identify spatial entities from folder structure
    const csvFiles = files.filter(f => f.type === 'csv');

    for (const file of csvFiles) {
      const parts = file.name.split('/').filter(p => p);
      const fileName = parts[parts.length - 1];

      // Parse sensor type from filename
      const sensorInfo = parseSensorFromFilename(fileName);

      if (sensorInfo) {
        // Extract room/space info from filename
        const spaceInfo = extractSpaceInfo(fileName);

        // Create or reference spatial entities
        if (spaceInfo.building && !spatialEntities.has(spaceInfo.building)) {
          spatialEntities.set(spaceInfo.building, {
            id: getId(),
            type: 'building',
            name: spaceInfo.building,
          });
        }

        if (spaceInfo.floor && !spatialEntities.has(`${spaceInfo.building}_${spaceInfo.floor}`)) {
          spatialEntities.set(`${spaceInfo.building}_${spaceInfo.floor}`, {
            id: getId(),
            type: 'floor',
            name: spaceInfo.floor,
            parent: spaceInfo.building,
          });
        }

        if (spaceInfo.room && !spatialEntities.has(`${spaceInfo.building}_${spaceInfo.room}`)) {
          spatialEntities.set(`${spaceInfo.building}_${spaceInfo.room}`, {
            id: getId(),
            type: 'room',
            name: spaceInfo.room,
            parent: spaceInfo.floor ? `${spaceInfo.building}_${spaceInfo.floor}` : spaceInfo.building,
          });
        }

        // Store sensor info
        const sensorKey = `${spaceInfo.building}_${spaceInfo.room}_${sensorInfo.type}_${sensors.size}`;
        sensors.set(sensorKey, {
          id: getId(),
          sensorType: sensorInfo.type,
          fileName: file.name,
          csvData: file.content,
        });
      }
    }

    // Create portfolio node if we have multiple buildings
    let portfolioId: string | null = null;
    const buildingEntities = Array.from(spatialEntities.values()).filter(e => e.type === 'building');

    if (buildingEntities.length > 1) {
      portfolioId = getId();
      nodes.push({
        id: portfolioId,
        type: 'custom',
        position: { x: 400, y: 50 },
        data: {
          label: 'Portfolio',
          baseType: 'spatialEntity',
          subType: 'portfolio',
          metadata: { name: 'Portfolio' },
        },
      });
    }

    // Create spatial entity nodes with layout
    let buildingX = 100;
    const buildingSpacing = 400;
    const floorSpacing = 300;
    const roomSpacing = 250;

    for (const [key, entity] of spatialEntities.entries()) {
      if (entity.type === 'building') {
        nodes.push({
          id: entity.id,
          type: 'custom',
          position: { x: buildingX, y: portfolioId ? 200 : 50 },
          data: {
            label: entity.name,
            baseType: 'spatialEntity',
            subType: 'building',
            metadata: { name: entity.name },
          },
        });

        if (portfolioId) {
          edges.push({
            id: `edge_${portfolioId}_${entity.id}`,
            source: portfolioId,
            target: entity.id,
            animated: false,
            style: { stroke: '#9CA3AF', strokeWidth: 2 },
          });
        }

        buildingX += buildingSpacing;
      }
    }

    // Add floors and rooms
    let roomY = portfolioId ? 500 : 350;
    for (const [key, entity] of spatialEntities.entries()) {
      if (entity.type === 'floor' && entity.parent) {
        const parentNode = nodes.find(n => spatialEntities.get(entity.parent!)?.id === n.id);
        if (parentNode) {
          nodes.push({
            id: entity.id,
            type: 'custom',
            position: { x: parentNode.position.x, y: parentNode.position.y + 200 },
            data: {
              label: entity.name,
              baseType: 'spatialEntity',
              subType: 'floor',
              metadata: { name: entity.name },
            },
          });

          edges.push({
            id: `edge_${parentNode.id}_${entity.id}`,
            source: parentNode.id,
            target: entity.id,
            animated: false,
            style: { stroke: '#9CA3AF', strokeWidth: 2 },
          });
        }
      }

      if (entity.type === 'room' && entity.parent) {
        const parentKey = entity.parent;
        const parentEntity = Array.from(spatialEntities.entries()).find(([k, v]) => k === parentKey)?.[1];
        const parentNode = nodes.find(n => parentEntity?.id === n.id);

        if (parentNode) {
          nodes.push({
            id: entity.id,
            type: 'custom',
            position: { x: parentNode.position.x - 100 + (nodes.filter(n => n.data.subType === 'room').length * 100), y: roomY },
            data: {
              label: entity.name,
              baseType: 'spatialEntity',
              subType: 'room',
              metadata: { name: entity.name },
            },
          });

          edges.push({
            id: `edge_${parentNode.id}_${entity.id}`,
            source: parentNode.id,
            target: entity.id,
            animated: false,
            style: { stroke: '#9CA3AF', strokeWidth: 2 },
          });
        }
      }
    }

    // Add sensors connected to rooms/buildings
    let sensorY = roomY + 200;
    for (const [key, sensor] of sensors.entries()) {
      const parts = key.split('_');
      const roomKey = `${parts[0]}_${parts[1]}`;
      const roomEntity = spatialEntities.get(roomKey);
      const parentNode = nodes.find(n => roomEntity?.id === n.id);

      if (parentNode) {
        const sensorNode: Node<NodeData> = {
          id: sensor.id,
          type: 'custom',
          position: {
            x: parentNode.position.x + (nodes.filter(n => n.data.baseType === 'sensor').length % 3) * 150 - 150,
            y: sensorY + Math.floor(nodes.filter(n => n.data.baseType === 'sensor').length / 3) * 100
          },
          data: {
            label: `${sensor.sensorType} sensor`,
            baseType: 'sensor',
            subType: sensor.sensorType,
            metadata: {
              name: `${sensor.sensorType} sensor`,
              metricMappings: detectMetricMappings(sensor.csvData, sensor.sensorType),
            },
            csvData: sensor.csvData,
            csvFile: sensor.fileName,
          },
        };

        nodes.push(sensorNode);

        // Create edge from room to sensor (reversed direction)
        const sensorConfig = { color: getSensorColor(sensor.sensorType) };
        edges.push({
          id: `edge_${parentNode.id}_${sensor.id}`,
          source: parentNode.id,
          target: sensor.id,
          animated: true,
          style: { stroke: sensorConfig.color, strokeWidth: 2 },
        });
      }
    }

    return { nodes, edges };
  };

  const parseSensorFromFilename = (filename: string): { type: SensorType } | null => {
    const lower = filename.toLowerCase();

    if (lower.includes('temperature') || lower.includes('temp')) return { type: 'temperature' };
    if (lower.includes('humidity') || lower.includes('rh')) return { type: 'humidity' };
    if (lower.includes('co2')) return { type: 'co2' };
    if (lower.includes('occupancy')) return { type: 'occupancy' };
    if (lower.includes('light') || lower.includes('lux')) return { type: 'light' };
    if (lower.includes('energy') || lower.includes('power')) return { type: 'energy' };

    return null;
  };

  const extractSpaceInfo = (filename: string): { building: string; floor?: string; room?: string } => {
    // Pattern: sensor_type_room_number.csv or sensor_type_building_floor_room.csv
    const lower = filename.toLowerCase().replace('.csv', '');
    const parts = lower.split('_');

    // Simple extraction: assume building_a, room_101 patterns
    let building = 'Building A';
    let room: string | undefined;
    let floor: string | undefined;

    for (const part of parts) {
      if (part.startsWith('building')) {
        building = part.charAt(0).toUpperCase() + part.slice(1).replace(/([a-z])([A-Z])/g, '$1 $2');
      }
      if (part.startsWith('room') || /^\d+$/.test(part)) {
        room = part.startsWith('room') ? part : `Room ${part}`;
      }
      if (part.startsWith('floor')) {
        floor = part.charAt(0).toUpperCase() + part.slice(1);
      }
    }

    return { building, floor, room: room || 'Main Room' };
  };

  const detectMetricMappings = (csvData: any[], sensorType: SensorType): any[] => {
    if (!csvData || csvData.length === 0) return [];

    const columns = Object.keys(csvData[0]).filter(
      col => col.toLowerCase() !== 'timestamp' && col.toLowerCase() !== 'time'
    );

    return columns.map(col => {
      const detectedType = autoDetectMetricType(col, sensorType);
      return {
        csvColumn: col,
        metricType: detectedType,
        unit: METRIC_TYPE_INFO[detectedType]?.defaultUnit || '',
      };
    });
  };

  const autoDetectMetricType = (columnName: string, fallbackType: SensorType): MetricType => {
    const lower = columnName.toLowerCase();

    // Use the same detection logic as CSVColumnMapper
    if (lower.includes('temp')) return 'temperature';
    if (lower.includes('co2')) return 'co2';
    if (lower.includes('humidity') || lower.includes('rh')) return 'humidity';
    if (lower.includes('occupancy')) return 'occupancy';
    if (lower.includes('light') || lower.includes('lux')) return 'illuminance';
    if (lower.includes('energy') || lower.includes('power')) return 'energy';

    // Fallback to sensor type
    return fallbackType as MetricType;
  };

  const getSensorColor = (sensorType: SensorType): string => {
    const colors: Record<SensorType, string> = {
      temperature: '#EF4444',
      humidity: '#06B6D4',
      co2: '#64748B',
      occupancy: '#8B5CF6',
      light: '#FBBF24',
      energy: '#22C55E',
    };
    return colors[sensorType] || '#9CA3AF';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Icons.FolderArchive size={24} />
            Upload Portfolio Zip
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            disabled={isProcessing}
          >
            <Icons.X size={24} />
          </button>
        </div>

        <div className="mb-4">
          <p className="text-gray-600 text-sm mb-2">
            Upload a zip file containing your portfolio structure with CSV sensor data files.
          </p>
          <p className="text-gray-500 text-xs">
            The system will automatically detect buildings, rooms, and sensors from file names and generate the flow diagram.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm flex items-start gap-2">
            <Icons.AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {progress && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-blue-700 text-sm flex items-center gap-2">
            <Icons.Loader2 size={16} className="animate-spin flex-shrink-0" />
            <span>{progress}</span>
          </div>
        )}

        <div className="mb-4">
          <label
            htmlFor="zip-upload"
            className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
              isProcessing
                ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
                : 'border-blue-300 bg-blue-50 hover:bg-blue-100'
            }`}
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <Icons.Upload className={`w-10 h-10 mb-2 ${isProcessing ? 'text-gray-400' : 'text-blue-500'}`} />
              <p className="mb-2 text-sm text-gray-700">
                <span className="font-semibold">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-gray-500">ZIP file only</p>
            </div>
            <input
              id="zip-upload"
              type="file"
              className="hidden"
              accept=".zip"
              onChange={handleFileUpload}
              disabled={isProcessing}
            />
          </label>
        </div>

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
