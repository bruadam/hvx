'use client';

import React from 'react';
import * as Icons from 'lucide-react';
import { SPATIAL_ENTITY_CONFIGS, SENSOR_CONFIGS, BaseNodeType } from '@/lib/nodeTypes';

interface NodeLibraryProps {
  onDragStart: (event: React.DragEvent, baseType: BaseNodeType) => void;
}

export default function NodeLibrary({ onDragStart }: NodeLibraryProps) {
  const renderNodeItem = (
    baseType: BaseNodeType,
    label: string,
    color: string,
    icon: string
  ) => {
    const IconComponent = Icons[icon as keyof typeof Icons] as React.ComponentType<any>;

    return (
      <div
        draggable
        onDragStart={(e) => onDragStart(e, baseType)}
        className="flex items-center gap-3 p-3 rounded-lg border-2 cursor-move hover:shadow-md transition-all bg-white"
        style={{ borderColor: color }}
      >
        <div
          className="p-2 rounded-md"
          style={{ backgroundColor: color + '30' }}
        >
          {IconComponent && <IconComponent size={20} style={{ color: color }} />}
        </div>
        <span className="text-sm font-medium">{label}</span>
      </div>
    );
  };

  return (
    <div className="w-64 bg-gray-50 border-l border-gray-200 p-4 overflow-y-auto">
      <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
        <Icons.Library size={20} />
        Component Library
      </h2>

      {/* Spatial Entity Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
          <Icons.Building2 size={16} />
          Spatial Entity
        </h3>
        <div className="space-y-2">
          {renderNodeItem(
            'spatialEntity',
            'Spatial Entity',
            '#3B82F6', // blue
            'MapPin'
          )}
        </div>
        <p className="text-xs text-gray-500 mt-2 italic">
          Type can be selected in properties: Portfolio, Building, Floor, or Room
        </p>
      </div>

      {/* Sensor Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
          <Icons.Gauge size={16} />
          Sensor
        </h3>
        <div className="space-y-2">
          {renderNodeItem(
            'sensor',
            'Sensor',
            '#10B981', // green
            'Activity'
          )}
        </div>
        <p className="text-xs text-gray-500 mt-2 italic">
          Type can be selected in properties: Temperature, Humidity, CO2, Occupancy, Light, or Energy
        </p>
      </div>

      {/* Instructions */}
      <div className="mt-6 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-xs text-blue-800 space-y-1">
          <span className="flex items-start gap-1">
            <Icons.Info size={14} className="mt-0.5 flex-shrink-0" />
            <span>Drag nodes onto the canvas. Double-click to configure properties and set specific type.</span>
          </span>
        </p>
      </div>

      {/* Available Types Reference */}
      <div className="mt-4 space-y-3">
        <details className="bg-white rounded-lg border border-gray-200">
          <summary className="p-2 cursor-pointer text-xs font-semibold text-gray-700 hover:bg-gray-50">
            Spatial Types
          </summary>
          <div className="p-2 space-y-1 text-xs text-gray-600">
            {Object.entries(SPATIAL_ENTITY_CONFIGS).map(([key, config]) => {
              const IconComponent = Icons[config.icon as keyof typeof Icons] as React.ComponentType<any>;
              return (
                <div key={key} className="flex items-center gap-2">
                  {IconComponent && <IconComponent size={12} style={{ color: config.color }} />}
                  <span>{config.label}</span>
                </div>
              );
            })}
          </div>
        </details>

        <details className="bg-white rounded-lg border border-gray-200">
          <summary className="p-2 cursor-pointer text-xs font-semibold text-gray-700 hover:bg-gray-50">
            Sensor Types
          </summary>
          <div className="p-2 space-y-1 text-xs text-gray-600">
            {Object.entries(SENSOR_CONFIGS).map(([key, config]) => {
              const IconComponent = Icons[config.icon as keyof typeof Icons] as React.ComponentType<any>;
              return (
                <div key={key} className="flex items-center gap-2">
                  {IconComponent && <IconComponent size={12} style={{ color: config.color }} />}
                  <span>{config.label}</span>
                </div>
              );
            })}
          </div>
        </details>
      </div>
    </div>
  );
}
