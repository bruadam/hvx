'use client';

import React, { useState, useEffect } from 'react';
import * as Icons from 'lucide-react';
import { MetricType, MetricMapping, METRIC_TYPE_INFO } from '@/lib/nodeTypes';

interface CSVColumnMapperProps {
  isOpen: boolean;
  onClose: () => void;
  csvData: any[];
  currentMappings: MetricMapping[];
  onSave: (mappings: MetricMapping[]) => void;
}

export default function CSVColumnMapper({
  isOpen,
  onClose,
  csvData,
  currentMappings,
  onSave,
}: CSVColumnMapperProps) {
  const [mappings, setMappings] = useState<MetricMapping[]>(currentMappings);
  const [availableColumns, setAvailableColumns] = useState<string[]>([]);

  useEffect(() => {
    if (csvData && csvData.length > 0) {
      const columns = Object.keys(csvData[0]).filter(
        col => col.toLowerCase() !== 'timestamp' && col.toLowerCase() !== 'time'
      );
      setAvailableColumns(columns);

      // Auto-detect metric types from column names if no mappings exist
      if (currentMappings.length === 0) {
        const autoMappings = columns.map(col => {
          const detectedType = detectMetricType(col);
          return {
            csvColumn: col,
            metricType: detectedType,
            unit: METRIC_TYPE_INFO[detectedType]?.defaultUnit || '',
          };
        });
        setMappings(autoMappings);
      }
    }
  }, [csvData, currentMappings]);

  const detectMetricType = (columnName: string): MetricType => {
    const lower = columnName.toLowerCase();

    // Temperature patterns
    if (lower.includes('temp') && lower.includes('supply')) return 'air_temperature_supply';
    if (lower.includes('temp') && lower.includes('return')) return 'air_temperature_return';
    if (lower.includes('temp') && lower.includes('outdoor')) return 'outdoor_temperature';
    if (lower.includes('temp') && lower.includes('setpoint')) return 'temperature_setpoint';
    if (lower.includes('temp')) return 'temperature';

    // CO2 patterns
    if (lower.includes('co2') && lower.includes('setpoint')) return 'co2_setpoint';
    if (lower.includes('co2')) return 'co2';

    // Humidity patterns
    if (lower.includes('humidity') && lower.includes('outdoor')) return 'outdoor_humidity';
    if (lower.includes('humidity') && lower.includes('setpoint')) return 'humidity_setpoint';
    if (lower.includes('humidity') || lower.includes('rh')) return 'humidity';

    // Energy patterns
    if (lower.includes('electricity') || lower.includes('electric')) return 'electricity';
    if (lower.includes('gas')) return 'gas';
    if (lower.includes('heat') && lower.includes('flux')) return 'heat_flux';
    if (lower.includes('heat')) return 'heat';
    if (lower.includes('cooling')) return 'cooling';
    if (lower.includes('power') && lower.includes('apparent')) return 'apparent_power';
    if (lower.includes('power') && lower.includes('reactive')) return 'reactive_power';
    if (lower.includes('power')) return 'power';
    if (lower.includes('energy')) return 'energy';

    // Water patterns
    if (lower.includes('water') && lower.includes('hot')) return 'water_hot';
    if (lower.includes('water') && lower.includes('cold')) return 'water_cold';
    if (lower.includes('water') && lower.includes('flow')) return 'water_flow';
    if (lower.includes('water') && lower.includes('temp') && lower.includes('supply')) return 'water_temperature_supply';
    if (lower.includes('water') && lower.includes('temp') && lower.includes('return')) return 'water_temperature_return';
    if (lower.includes('water')) return 'water';

    // Airflow patterns
    if (lower.includes('airflow') && lower.includes('supply')) return 'airflow_supply';
    if (lower.includes('airflow') && lower.includes('return')) return 'airflow_return';
    if (lower.includes('airflow')) return 'airflow';

    // Occupancy patterns
    if (lower.includes('occupancy') && lower.includes('percent')) return 'occupancy_percent';
    if (lower.includes('occupancy') && lower.includes('design')) return 'design_occupancy';
    if (lower.includes('occupancy')) return 'occupancy';

    // Light patterns
    if (lower.includes('illuminance')) return 'illuminance';
    if (lower.includes('lux')) return 'lux';
    if (lower.includes('light')) return 'light_level';

    // Air quality patterns
    if (lower.includes('voc')) return 'voc';
    if (lower.includes('pm2.5') || lower.includes('pm25')) return 'pm2_5';
    if (lower.includes('pm10')) return 'pm10';
    if (lower.includes('noise') || lower.includes('sound')) return 'noise';

    // Pressure patterns
    if (lower.includes('pressure') && lower.includes('diff')) return 'differential_pressure';
    if (lower.includes('pressure') && lower.includes('barometric')) return 'barometric_pressure';
    if (lower.includes('pressure')) return 'pressure';

    // Weather patterns
    if (lower.includes('wind') && lower.includes('speed')) return 'wind_speed';
    if (lower.includes('wind') && lower.includes('direction')) return 'wind_direction';
    if (lower.includes('solar')) return 'solar_irradiance';

    // HVAC control patterns
    if (lower.includes('valve')) return 'valve_position';
    if (lower.includes('damper')) return 'damper_position';

    // Motion
    if (lower.includes('motion')) return 'motion';

    return 'other';
  };

  const addMapping = () => {
    if (availableColumns.length > 0) {
      const unusedColumn = availableColumns.find(
        col => !mappings.some(m => m.csvColumn === col)
      ) || availableColumns[0];

      setMappings([
        ...mappings,
        {
          csvColumn: unusedColumn,
          metricType: 'other',
          unit: '',
        },
      ]);
    }
  };

  const removeMapping = (index: number) => {
    setMappings(mappings.filter((_, i) => i !== index));
  };

  const updateMapping = (index: number, field: keyof MetricMapping, value: any) => {
    const updated = [...mappings];
    updated[index] = { ...updated[index], [field]: value };

    // Auto-update unit when metric type changes
    if (field === 'metricType') {
      updated[index].unit = METRIC_TYPE_INFO[value as MetricType]?.defaultUnit || '';
    }

    setMappings(updated);
  };

  const handleSave = () => {
    onSave(mappings);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Icons.MapPin size={24} />
            Map CSV Columns to Metric Types
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Icons.X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          <p className="text-gray-600 mb-4">
            Map each CSV column to a metric type. The system has auto-detected types based on column names.
          </p>

          {mappings.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Icons.AlertCircle size={48} className="mx-auto mb-4 opacity-50" />
              <p>No columns mapped yet. Click &quot;Add Mapping&quot; to start.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {mappings.map((mapping, index) => (
                <div
                  key={index}
                  className="p-4 border border-gray-200 rounded-lg bg-gray-50 flex gap-4 items-center"
                >
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      CSV Column
                    </label>
                    <select
                      value={mapping.csvColumn}
                      onChange={(e) => updateMapping(index, 'csvColumn', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {availableColumns.map(col => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Metric Type
                    </label>
                    <select
                      value={mapping.metricType}
                      onChange={(e) => updateMapping(index, 'metricType', e.target.value as MetricType)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {(Object.keys(METRIC_TYPE_INFO) as MetricType[]).map(type => (
                        <option key={type} value={type}>
                          {METRIC_TYPE_INFO[type].label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="w-32">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Unit
                    </label>
                    <input
                      type="text"
                      value={mapping.unit || ''}
                      onChange={(e) => updateMapping(index, 'unit', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. °C"
                    />
                  </div>

                  <button
                    onClick={() => removeMapping(index)}
                    className="mt-6 p-2 text-red-600 hover:bg-red-50 rounded-full transition-colors"
                    title="Remove mapping"
                  >
                    <Icons.Trash2 size={20} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={addMapping}
            disabled={availableColumns.length === 0}
            className="mt-4 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Icons.Plus size={16} />
            Add Mapping
          </button>
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-between items-center bg-gray-50">
          <div className="text-sm text-gray-600">
            {mappings.length} metric{mappings.length !== 1 ? 's' : ''} mapped
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Icons.Save size={16} />
              Save Mappings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
