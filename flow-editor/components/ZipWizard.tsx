'use client';

import React, { useState } from 'react';
import * as Icons from 'lucide-react';
import { Node, Edge } from 'reactflow';
import { NodeData, SpatialEntityType, SensorType } from '@/lib/nodeTypes';

// Hierarchical structure from zip file
interface Portfolio {
  name: string;
  metadata?: any;
  buildings: Building[];
}

interface Building {
  name: string;
  folder: string;
  metadata?: any;
  floors: Floor[];
  sensors: SensorFile[];
}

interface Floor {
  name: string;
  folder: string;
  metadata?: any;
  rooms: Room[];
  sensors: SensorFile[];
}

interface Room {
  name: string;
  folder: string;
  metadata?: any;
  sensors: SensorFile[];
}

interface SensorFile {
  name: string;
  fileName: string;
  sensorType: SensorType;
  csvData: any[];
  metricColumns: string[];
}

interface ZipWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (nodes: Node<NodeData>[], edges: Edge[]) => void;
  parsedStructure: Portfolio | null;
}

type WizardStep = 'portfolio' | 'buildings' | 'floors' | 'rooms' | 'review';

export default function ZipWizard({
  isOpen,
  onClose,
  onGenerate,
  parsedStructure,
}: ZipWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('portfolio');
  const [currentBuildingIndex, setCurrentBuildingIndex] = useState(0);
  const [currentFloorIndex, setCurrentFloorIndex] = useState(0);

  const [editedPortfolio, setEditedPortfolio] = useState<Portfolio | null>(parsedStructure);

  if (!isOpen || !editedPortfolio) return null;

  const currentBuilding = editedPortfolio.buildings[currentBuildingIndex];
  const currentFloor = currentBuilding?.floors[currentFloorIndex];

  const handleNext = () => {
    if (currentStep === 'portfolio') {
      setCurrentStep('buildings');
    } else if (currentStep === 'buildings') {
      if (currentBuildingIndex < editedPortfolio.buildings.length - 1) {
        setCurrentBuildingIndex(currentBuildingIndex + 1);
      } else {
        setCurrentStep('floors');
        setCurrentBuildingIndex(0);
        setCurrentFloorIndex(0);
      }
    } else if (currentStep === 'floors') {
      const building = editedPortfolio.buildings[currentBuildingIndex];
      if (currentFloorIndex < building.floors.length - 1) {
        setCurrentFloorIndex(currentFloorIndex + 1);
      } else if (currentBuildingIndex < editedPortfolio.buildings.length - 1) {
        setCurrentBuildingIndex(currentBuildingIndex + 1);
        setCurrentFloorIndex(0);
      } else {
        setCurrentStep('rooms');
        setCurrentBuildingIndex(0);
        setCurrentFloorIndex(0);
      }
    } else if (currentStep === 'rooms') {
      setCurrentStep('review');
    }
  };

  const handleBack = () => {
    if (currentStep === 'buildings') {
      if (currentBuildingIndex > 0) {
        setCurrentBuildingIndex(currentBuildingIndex - 1);
      } else {
        setCurrentStep('portfolio');
      }
    } else if (currentStep === 'floors') {
      if (currentFloorIndex > 0) {
        setCurrentFloorIndex(currentFloorIndex - 1);
      } else if (currentBuildingIndex > 0) {
        setCurrentBuildingIndex(currentBuildingIndex - 1);
        const prevBuilding = editedPortfolio.buildings[currentBuildingIndex - 1];
        setCurrentFloorIndex(prevBuilding.floors.length - 1);
      } else {
        setCurrentStep('buildings');
        setCurrentBuildingIndex(editedPortfolio.buildings.length - 1);
      }
    } else if (currentStep === 'rooms') {
      setCurrentStep('floors');
    } else if (currentStep === 'review') {
      setCurrentStep('rooms');
    }
  };

  const handleGenerate = () => {
    if (!editedPortfolio) return;

    const { nodes, edges } = generateFlowFromStructure(editedPortfolio);
    onGenerate(nodes, edges);
    onClose();
  };

  const updatePortfolioMetadata = (key: string, value: any) => {
    if (!editedPortfolio) return;
    setEditedPortfolio({
      ...editedPortfolio,
      metadata: { ...editedPortfolio.metadata, [key]: value },
    });
  };

  const updateBuildingMetadata = (buildingIndex: number, key: string, value: any) => {
    if (!editedPortfolio) return;
    const updatedBuildings = [...editedPortfolio.buildings];
    updatedBuildings[buildingIndex] = {
      ...updatedBuildings[buildingIndex],
      metadata: { ...updatedBuildings[buildingIndex].metadata, [key]: value },
    };
    setEditedPortfolio({ ...editedPortfolio, buildings: updatedBuildings });
  };

  const renderPortfolioStep = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Portfolio Information</h3>
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Portfolio Name
          </label>
          <input
            type="text"
            value={editedPortfolio?.name || ''}
            onChange={(e) => {
              if (editedPortfolio) {
                setEditedPortfolio({ ...editedPortfolio, name: e.target.value });
              }
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={editedPortfolio?.metadata?.description || ''}
            onChange={(e) => updatePortfolioMetadata('description', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
        </div>
        <div className="bg-blue-50 p-3 rounded-md">
          <p className="text-sm text-blue-800">
            <Icons.Info className="inline mr-1" size={14} />
            Found {editedPortfolio?.buildings.length} building(s) in the zip file
          </p>
        </div>
      </div>
    </div>
  );

  const renderBuildingStep = () => {
    if (!currentBuilding) return null;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">
            Building {currentBuildingIndex + 1} of {editedPortfolio!.buildings.length}
          </h3>
          <span className="text-sm text-gray-500">{currentBuilding.folder}</span>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Building Name
            </label>
            <input
              type="text"
              value={currentBuilding.name}
              onChange={(e) => {
                const updated = [...editedPortfolio!.buildings];
                updated[currentBuildingIndex] = { ...updated[currentBuildingIndex], name: e.target.value };
                setEditedPortfolio({ ...editedPortfolio!, buildings: updated });
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Area (m²)
              </label>
              <input
                type="number"
                value={currentBuilding.metadata?.area_m2 || ''}
                onChange={(e) => updateBuildingMetadata(currentBuildingIndex, 'area_m2', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Country Code
              </label>
              <input
                type="text"
                value={currentBuilding.metadata?.country || ''}
                onChange={(e) => updateBuildingMetadata(currentBuildingIndex, 'country', e.target.value.toUpperCase())}
                placeholder="DK"
                maxLength={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Building Type
            </label>
            <select
              value={currentBuilding.metadata?.building_type || 'office'}
              onChange={(e) => updateBuildingMetadata(currentBuildingIndex, 'building_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="office">Office</option>
              <option value="residential">Residential</option>
              <option value="education">Education</option>
              <option value="healthcare">Healthcare</option>
              <option value="commercial">Commercial</option>
              <option value="industrial">Industrial</option>
            </select>
          </div>
          <div className="bg-gray-50 p-3 rounded-md space-y-1">
            <p className="text-sm font-medium text-gray-700">Content:</p>
            <p className="text-sm text-gray-600">• {currentBuilding.floors.length} floor(s)</p>
            <p className="text-sm text-gray-600">• {currentBuilding.sensors.length} building-level sensor(s)</p>
          </div>
        </div>
      </div>
    );
  };

  const renderFloorStep = () => {
    if (!currentBuilding || !currentFloor) return null;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">
            {currentBuilding.name} - Floor {currentFloorIndex + 1} of {currentBuilding.floors.length}
          </h3>
          <span className="text-sm text-gray-500">{currentFloor.folder}</span>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Floor Name
            </label>
            <input
              type="text"
              value={currentFloor.name}
              onChange={(e) => {
                const updatedBuildings = [...editedPortfolio!.buildings];
                updatedBuildings[currentBuildingIndex].floors[currentFloorIndex].name = e.target.value;
                setEditedPortfolio({ ...editedPortfolio!, buildings: updatedBuildings });
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Floor Number
            </label>
            <input
              type="number"
              value={currentFloor.metadata?.floor_number || ''}
              onChange={(e) => {
                const updatedBuildings = [...editedPortfolio!.buildings];
                updatedBuildings[currentBuildingIndex].floors[currentFloorIndex].metadata = {
                  ...updatedBuildings[currentBuildingIndex].floors[currentFloorIndex].metadata,
                  floor_number: parseInt(e.target.value),
                };
                setEditedPortfolio({ ...editedPortfolio!, buildings: updatedBuildings });
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="bg-gray-50 p-3 rounded-md space-y-1">
            <p className="text-sm font-medium text-gray-700">Content:</p>
            <p className="text-sm text-gray-600">• {currentFloor.rooms.length} room(s)</p>
            <p className="text-sm text-gray-600">• {currentFloor.sensors.length} floor-level sensor(s)</p>
          </div>
        </div>
      </div>
    );
  };

  const renderRoomStep = () => {
    if (!currentBuilding) return null;

    // Collect all rooms from all floors
    const allRooms: Array<{ building: any; floor: any; room: any; buildingIdx: number; floorIdx: number; roomIdx: number }> = [];
    editedPortfolio!.buildings.forEach((building, bIdx) => {
      building.floors.forEach((floor, fIdx) => {
        floor.rooms.forEach((room, rIdx) => {
          allRooms.push({ building, floor, room, buildingIdx: bIdx, floorIdx: fIdx, roomIdx: rIdx });
        });
      });
    });

    if (allRooms.length === 0) {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Rooms</h3>
          <div className="bg-yellow-50 p-4 rounded-md">
            <p className="text-sm text-yellow-800">
              <Icons.AlertCircle className="inline mr-1" size={16} />
              No rooms with sensors found. Sensors are attached directly to floors or buildings.
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-4 max-h-96 overflow-y-auto">
        <h3 className="text-lg font-semibold sticky top-0 bg-white pb-2">
          Rooms ({allRooms.length} total)
        </h3>
        <div className="space-y-3">
          {allRooms.map(({ building, floor, room, buildingIdx, floorIdx, roomIdx }, idx) => (
            <div key={idx} className="border rounded-md p-3">
              <div className="text-xs text-gray-500 mb-2">
                {building.name} → {floor.name}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Room Name
                  </label>
                  <input
                    type="text"
                    value={room.name}
                    onChange={(e) => {
                      const updated = [...editedPortfolio!.buildings];
                      updated[buildingIdx].floors[floorIdx].rooms[roomIdx].name = e.target.value;
                      setEditedPortfolio({ ...editedPortfolio!, buildings: updated });
                    }}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Area (m²)
                  </label>
                  <input
                    type="number"
                    value={room.metadata?.area_m2 || ''}
                    onChange={(e) => {
                      const updated = [...editedPortfolio!.buildings];
                      updated[buildingIdx].floors[floorIdx].rooms[roomIdx].metadata = {
                        ...updated[buildingIdx].floors[floorIdx].rooms[roomIdx].metadata,
                        area_m2: parseFloat(e.target.value),
                      };
                      setEditedPortfolio({ ...editedPortfolio!, buildings: updated });
                    }}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {room.sensors.length} sensor(s): {room.sensors.map(s => s.sensorType).join(', ')}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderReviewStep = () => (
    <div className="space-y-4 max-h-96 overflow-y-auto">
      <h3 className="text-lg font-semibold sticky top-0 bg-white pb-2">Review Structure</h3>
      <div className="space-y-3">
        <div className="border-l-4 border-purple-500 pl-3">
          <div className="font-medium">{editedPortfolio?.name}</div>
          <div className="text-sm text-gray-500">Portfolio</div>
        </div>
        {editedPortfolio?.buildings.map((building, bIdx) => (
          <div key={bIdx} className="ml-6 space-y-2">
            <div className="border-l-4 border-blue-500 pl-3">
              <div className="font-medium">{building.name}</div>
              <div className="text-sm text-gray-500">
                Building • {building.metadata?.area_m2}m² • {building.metadata?.country}
              </div>
            </div>
            {building.floors.map((floor, fIdx) => (
              <div key={fIdx} className="ml-6 space-y-1">
                <div className="border-l-4 border-green-500 pl-3">
                  <div className="font-medium">{floor.name}</div>
                  <div className="text-sm text-gray-500">Floor • {floor.rooms.length} rooms</div>
                </div>
                {floor.rooms.map((room, rIdx) => (
                  <div key={rIdx} className="ml-6">
                    <div className="border-l-4 border-amber-500 pl-3">
                      <div className="font-medium text-sm">{room.name}</div>
                      <div className="text-xs text-gray-500">{room.sensors.length} sensors</div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Icons.FileArchive size={24} />
            Portfolio Import Wizard
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Icons.X size={24} />
          </button>
        </div>

        {/* Progress */}
        <div className="px-6 py-4 bg-gray-50 border-b">
          <div className="flex items-center justify-between text-sm">
            <Step label="Portfolio" active={currentStep === 'portfolio'} completed={['buildings', 'floors', 'rooms', 'review'].includes(currentStep)} />
            <div className="flex-1 h-px bg-gray-300 mx-2" />
            <Step label="Buildings" active={currentStep === 'buildings'} completed={['floors', 'rooms', 'review'].includes(currentStep)} />
            <div className="flex-1 h-px bg-gray-300 mx-2" />
            <Step label="Floors" active={currentStep === 'floors'} completed={['rooms', 'review'].includes(currentStep)} />
            <div className="flex-1 h-px bg-gray-300 mx-2" />
            <Step label="Rooms" active={currentStep === 'rooms'} completed={currentStep === 'review'} />
            <div className="flex-1 h-px bg-gray-300 mx-2" />
            <Step label="Review" active={currentStep === 'review'} completed={false} />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentStep === 'portfolio' && renderPortfolioStep()}
          {currentStep === 'buildings' && renderBuildingStep()}
          {currentStep === 'floors' && renderFloorStep()}
          {currentStep === 'rooms' && renderRoomStep()}
          {currentStep === 'review' && renderReviewStep()}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t bg-gray-50">
          <button
            onClick={handleBack}
            disabled={currentStep === 'portfolio'}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Icons.ChevronLeft size={16} />
            Back
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            {currentStep === 'review' ? (
              <button
                onClick={handleGenerate}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <Icons.Check size={16} />
                Generate Flow
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                Next
                <Icons.ChevronRight size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Step({ label, active, completed }: { label: string; active: boolean; completed: boolean }) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
          completed
            ? 'bg-green-500 text-white'
            : active
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-500'
        }`}
      >
        {completed ? <Icons.Check size={16} /> : label[0]}
      </div>
      <span className={`text-xs mt-1 ${active ? 'font-medium text-gray-900' : 'text-gray-500'}`}>
        {label}
      </span>
    </div>
  );
}

function generateFlowFromStructure(portfolio: Portfolio): { nodes: Node<NodeData>[], edges: Edge[] } {
  const nodes: Node<NodeData>[] = [];
  const edges: Edge[] = [];

  let nodeIdCounter = 0;
  const getId = () => `node_${nodeIdCounter++}`;

  // Create portfolio node
  const portfolioId = getId();
  nodes.push({
    id: portfolioId,
    type: 'custom',
    position: { x: 400, y: 50 },
    data: {
      label: portfolio.name,
      baseType: 'spatialEntity',
      subType: 'portfolio',
      metadata: { name: portfolio.name, ...portfolio.metadata },
    },
  });

  // Create building nodes
  let buildingX = 100;
  portfolio.buildings.forEach((building) => {
    const buildingId = getId();
    nodes.push({
      id: buildingId,
      type: 'custom',
      position: { x: buildingX, y: 200 },
      data: {
        label: building.name,
        baseType: 'spatialEntity',
        subType: 'building',
        metadata: { name: building.name, ...building.metadata },
      },
    });

    edges.push({
      id: `edge_${portfolioId}_${buildingId}`,
      source: portfolioId,
      target: buildingId,
      animated: false,
      style: { stroke: '#9CA3AF', strokeWidth: 2 },
    });

    buildingX += 400;

    // Add building-level sensors
    building.sensors.forEach((sensor, sIdx) => {
      const sensorId = getId();
      nodes.push({
        id: sensorId,
        type: 'custom',
        position: { x: parseInt(buildingId.split('_')[1]) * 50 + sIdx * 150, y: 350 },
        data: {
          label: sensor.name,
          baseType: 'sensor',
          subType: sensor.sensorType,
          metadata: { name: sensor.name },
          csvData: sensor.csvData,
          csvFile: sensor.fileName,
        },
      });

      edges.push({
        id: `edge_${buildingId}_${sensorId}`,
        source: buildingId,
        target: sensorId,
        animated: true,
        style: { stroke: getSensorColor(sensor.sensorType), strokeWidth: 2 },
      });
    });

    // Create floor nodes
    let floorY = 500;
    building.floors.forEach((floor) => {
      const floorId = getId();
      nodes.push({
        id: floorId,
        type: 'custom',
        position: { x: buildingX - 400, y: floorY },
        data: {
          label: floor.name,
          baseType: 'spatialEntity',
          subType: 'floor',
          metadata: { name: floor.name, ...floor.metadata },
        },
      });

      edges.push({
        id: `edge_${buildingId}_${floorId}`,
        source: buildingId,
        target: floorId,
        animated: false,
        style: { stroke: '#9CA3AF', strokeWidth: 2 },
      });

      floorY += 300;

      // Create room nodes
      let roomX = buildingX - 500;
      floor.rooms.forEach((room) => {
        const roomId = getId();
        nodes.push({
          id: roomId,
          type: 'custom',
          position: { x: roomX, y: floorY },
          data: {
            label: room.name,
            baseType: 'spatialEntity',
            subType: 'room',
            metadata: { name: room.name, ...room.metadata },
          },
        });

        edges.push({
          id: `edge_${floorId}_${roomId}`,
          source: floorId,
          target: roomId,
          animated: false,
          style: { stroke: '#9CA3AF', strokeWidth: 2 },
        });

        roomX += 200;

        // Add room sensors
        let sensorY = floorY + 150;
        room.sensors.forEach((sensor) => {
          const sensorId = getId();
          nodes.push({
            id: sensorId,
            type: 'custom',
            position: { x: roomX - 200, y: sensorY },
            data: {
              label: sensor.name,
              baseType: 'sensor',
              subType: sensor.sensorType,
              metadata: { name: sensor.name },
              csvData: sensor.csvData,
              csvFile: sensor.fileName,
            },
          });

          edges.push({
            id: `edge_${roomId}_${sensorId}`,
            source: roomId,
            target: sensorId,
            animated: true,
            style: { stroke: getSensorColor(sensor.sensorType), strokeWidth: 2 },
          });

          sensorY += 100;
        });
      });
    });
  });

  return { nodes, edges };
}

function getSensorColor(sensorType: SensorType): string {
  const colors: Record<SensorType, string> = {
    indoor_climate: '#EF4444',
    weather: '#06B6D4',
    energy_consumption: '#22C55E',
    occupancy: '#8B5CF6',
    power: '#F59E0B',
    water: '#3B82F6',
  };
  return colors[sensorType] || '#9CA3AF';
}
