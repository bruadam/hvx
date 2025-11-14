'use client';

import React, { useState, useEffect } from 'react';
import * as Icons from 'lucide-react';
import { NodeData, NodeMetadata, SpatialEntityType, SensorType, SPATIAL_ENTITY_CONFIGS, SENSOR_CONFIGS } from '@/lib/nodeTypes';

interface NodePropertiesModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodeData: NodeData;
  onSave: (updatedData: Partial<NodeData>) => void;
}

export default function NodePropertiesModal({
  isOpen,
  onClose,
  nodeData,
  onSave,
}: NodePropertiesModalProps) {
  const [label, setLabel] = useState(nodeData.label);
  const [subType, setSubType] = useState(nodeData.subType);
  const [metadata, setMetadata] = useState<NodeMetadata>(nodeData.metadata);
  const [customFieldKey, setCustomFieldKey] = useState('');
  const [customFieldValue, setCustomFieldValue] = useState('');

  useEffect(() => {
    if (isOpen) {
      setLabel(nodeData.label);
      setSubType(nodeData.subType);
      setMetadata(nodeData.metadata);
    }
  }, [isOpen, nodeData]);

  const handleSave = () => {
    onSave({
      label,
      subType,
      metadata,
    });
    onClose();
  };

  const updateMetadata = (field: keyof NodeMetadata, value: any) => {
    setMetadata((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const addCustomField = () => {
    if (!customFieldKey) return;

    setMetadata((prev) => ({
      ...prev,
      customFields: {
        ...prev.customFields,
        [customFieldKey]: customFieldValue,
      },
    }));
    setCustomFieldKey('');
    setCustomFieldValue('');
  };

  const removeCustomField = (key: string) => {
    setMetadata((prev) => {
      const { [key]: removed, ...rest } = prev.customFields || {};
      return {
        ...prev,
        customFields: rest,
      };
    });
  };

  if (!isOpen) return null;

  const isSpatialEntity = nodeData.baseType === 'spatialEntity';
  const availableSubTypes = isSpatialEntity
    ? Object.keys(SPATIAL_ENTITY_CONFIGS)
    : Object.keys(SENSOR_CONFIGS);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Icons.Settings size={24} className="text-blue-600" />
            <h2 className="text-2xl font-bold">Node Properties</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Icons.X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Basic Information */}
            <section>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Icons.Tag size={18} />
                Basic Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Label
                  </label>
                  <input
                    type="text"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Node label"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type
                  </label>
                  <select
                    value={subType}
                    onChange={(e) => setSubType(e.target.value as SpatialEntityType | SensorType)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {availableSubTypes.map((type) => (
                      <option key={type} value={type}>
                        {isSpatialEntity
                          ? SPATIAL_ENTITY_CONFIGS[type as SpatialEntityType].label
                          : SENSOR_CONFIGS[type as SensorType].label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    value={metadata.name || ''}
                    onChange={(e) => updateMetadata('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={metadata.description || ''}
                    onChange={(e) => updateMetadata('description', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="Optional description"
                  />
                </div>
              </div>
            </section>

            {/* Spatial Entity Specific Fields */}
            {isSpatialEntity && (
              <section>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Icons.Building2 size={18} />
                  Spatial Properties
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Area (m²)
                    </label>
                    <input
                      type="number"
                      value={metadata.area || ''}
                      onChange={(e) => updateMetadata('area', parseFloat(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Volume (m³)
                    </label>
                    <input
                      type="number"
                      value={metadata.volume || ''}
                      onChange={(e) => updateMetadata('volume', parseFloat(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Floor Number
                    </label>
                    <input
                      type="number"
                      value={metadata.floorNumber || ''}
                      onChange={(e) => updateMetadata('floorNumber', parseInt(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Capacity
                    </label>
                    <input
                      type="number"
                      value={metadata.capacity || ''}
                      onChange={(e) => updateMetadata('capacity', parseInt(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Max occupancy"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Address
                    </label>
                    <input
                      type="text"
                      value={metadata.address || ''}
                      onChange={(e) => updateMetadata('address', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Full address"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Building Type
                    </label>
                    <input
                      type="text"
                      value={metadata.buildingType || ''}
                      onChange={(e) => updateMetadata('buildingType', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g., Office, Residential, School"
                    />
                  </div>
                </div>
              </section>
            )}

            {/* Sensor Specific Fields */}
            {!isSpatialEntity && (
              <section>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Icons.Gauge size={18} />
                  Sensor Properties
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Unit
                    </label>
                    <input
                      type="text"
                      value={metadata.unit || ''}
                      onChange={(e) => updateMetadata('unit', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g., °C, %, ppm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Accuracy
                    </label>
                    <input
                      type="number"
                      value={metadata.accuracy || ''}
                      onChange={(e) => updateMetadata('accuracy', parseFloat(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="±0.00"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Value
                    </label>
                    <input
                      type="number"
                      value={metadata.minValue || ''}
                      onChange={(e) => updateMetadata('minValue', parseFloat(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Value
                    </label>
                    <input
                      type="number"
                      value={metadata.maxValue || ''}
                      onChange={(e) => updateMetadata('maxValue', parseFloat(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Measurement Interval (seconds)
                    </label>
                    <input
                      type="number"
                      value={metadata.measurementInterval || ''}
                      onChange={(e) => updateMetadata('measurementInterval', parseInt(e.target.value) || undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="60"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Calibration Date
                    </label>
                    <input
                      type="date"
                      value={metadata.calibrationDate || ''}
                      onChange={(e) => updateMetadata('calibrationDate', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Manufacturer
                    </label>
                    <input
                      type="text"
                      value={metadata.manufacturer || ''}
                      onChange={(e) => updateMetadata('manufacturer', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Manufacturer name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Model
                    </label>
                    <input
                      type="text"
                      value={metadata.model || ''}
                      onChange={(e) => updateMetadata('model', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Model number"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Serial Number
                    </label>
                    <input
                      type="text"
                      value={metadata.serialNumber || ''}
                      onChange={(e) => updateMetadata('serialNumber', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Serial number"
                    />
                  </div>
                </div>
              </section>
            )}

            {/* Custom Fields */}
            <section>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Icons.Plus size={18} />
                Custom Fields
              </h3>

              {/* Existing Custom Fields */}
              {metadata.customFields && Object.keys(metadata.customFields).length > 0 && (
                <div className="mb-4 space-y-2">
                  {Object.entries(metadata.customFields).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2 p-2 bg-gray-50 rounded-md">
                      <span className="font-medium text-sm flex-1">{key}:</span>
                      <span className="text-sm text-gray-600">{String(value)}</span>
                      <button
                        onClick={() => removeCustomField(key)}
                        className="p-1 hover:bg-red-100 rounded text-red-600"
                      >
                        <Icons.Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add New Custom Field */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customFieldKey}
                  onChange={(e) => setCustomFieldKey(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Field name"
                />
                <input
                  type="text"
                  value={customFieldValue}
                  onChange={(e) => setCustomFieldValue(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Field value"
                />
                <button
                  onClick={addCustomField}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                >
                  <Icons.Plus size={16} />
                </button>
              </div>
            </section>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Icons.Save size={16} />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
