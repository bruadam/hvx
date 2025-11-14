'use client';

import React, { useState } from 'react';
import {
  Calculator,
  TrendingUp,
  Activity,
  AlertCircle,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronRight,
  Thermometer,
  Wind,
  Droplets,
  Users,
  BarChart3
} from 'lucide-react';

interface SensorStats {
  sensorCount: number;
  connectedSensors: string[];
  sensorTypes: Record<string, number>;
  dataPointsTotal: number;
  timeRange?: {
    start: string;
    end: string;
  };
}

interface StandardResult {
  standardId: string;
  standardName: string;
  status: 'compliant' | 'non_compliant' | 'warning' | 'not_computed';
  category?: string;
  complianceRate?: number;
  violations?: number;
  summary?: string;
  details?: Record<string, any>;
}

interface SimulationResult {
  simulationId: string;
  simulationName: string;
  status: 'completed' | 'failed' | 'not_computed';
  summary?: string;
  results?: Record<string, any>;
}

interface StatisticsData {
  sensorStats?: SensorStats;
  standardsResults?: StandardResult[];
  simulationResults?: SimulationResult[];
  lastComputedAt?: string;
}

interface StatisticsPanelProps {
  nodeId: string;
  nodeLabel: string;
  nodeType: 'portfolio' | 'building' | 'floor' | 'room';
  statistics?: StatisticsData;
  onComputeSensorStats: () => Promise<void>;
  onComputeStandards: () => Promise<void>;
  onComputeSimulations: () => Promise<void>;
  isComputing?: boolean;
}

export default function StatisticsPanel({
  nodeId,
  nodeLabel,
  nodeType,
  statistics,
  onComputeSensorStats,
  onComputeStandards,
  onComputeSimulations,
  isComputing = false,
}: StatisticsPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['sensors']));
  const [computingSection, setComputingSection] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handleCompute = async (section: string, computeFn: () => Promise<void>) => {
    setComputingSection(section);
    try {
      await computeFn();
    } finally {
      setComputingSection(null);
    }
  };

  const sensorStats = statistics?.sensorStats;
  const standardsResults = statistics?.standardsResults || [];
  const simulationResults = statistics?.simulationResults || [];

  return (
    <div className="absolute right-0 top-0 w-96 h-full bg-white border-l border-gray-300 overflow-y-auto shadow-lg">
      {/* Header */}
      <div className="sticky top-0 bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 z-10">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Statistics: {nodeLabel}
        </h2>
        <p className="text-sm text-blue-100 mt-1">
          {nodeType.charAt(0).toUpperCase() + nodeType.slice(1)} Analysis
        </p>
        {statistics?.lastComputedAt && (
          <p className="text-xs text-blue-100 mt-2">
            Last updated: {new Date(statistics.lastComputedAt).toLocaleString()}
          </p>
        )}
      </div>

      {/* Sensor Statistics Section */}
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection('sensors')}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            {expandedSections.has('sensors') ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
            <Activity className="w-5 h-5 text-green-600" />
            <span className="font-semibold">Sensor Statistics</span>
          </div>
          {sensorStats && (
            <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">
              {sensorStats.sensorCount} sensors
            </span>
          )}
        </button>

        {expandedSections.has('sensors') && (
          <div className="px-4 pb-4 bg-gray-50">
            {sensorStats ? (
              <div className="space-y-3 mt-3">
                <div className="bg-white rounded p-3 shadow-sm">
                  <p className="text-sm font-medium text-gray-700 mb-2">Connected Sensors</p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(sensorStats.sensorTypes).map(([type, count]) => (
                      <div key={type} className="flex items-center gap-2 text-sm">
                        {type === 'temperature' && <Thermometer className="w-4 h-4 text-red-500" />}
                        {type === 'co2' && <Wind className="w-4 h-4 text-blue-500" />}
                        {type === 'humidity' && <Droplets className="w-4 h-4 text-cyan-500" />}
                        {type === 'occupancy' && <Users className="w-4 h-4 text-purple-500" />}
                        <span className="text-gray-600">{type}: {count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded p-3 shadow-sm">
                  <p className="text-sm font-medium text-gray-700 mb-1">Total Data Points</p>
                  <p className="text-2xl font-bold text-blue-600">{sensorStats.dataPointsTotal.toLocaleString()}</p>
                </div>

                {sensorStats.timeRange && (
                  <div className="bg-white rounded p-3 shadow-sm">
                    <p className="text-sm font-medium text-gray-700 mb-1">Time Range</p>
                    <p className="text-xs text-gray-600">
                      {new Date(sensorStats.timeRange.start).toLocaleDateString()} - {new Date(sensorStats.timeRange.end).toLocaleDateString()}
                    </p>
                  </div>
                )}

                <button
                  onClick={() => handleCompute('sensors', onComputeSensorStats)}
                  disabled={computingSection === 'sensors'}
                  className="w-full mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                >
                  <Calculator className="w-4 h-4" />
                  {computingSection === 'sensors' ? 'Computing...' : 'Recompute Stats'}
                </button>
              </div>
            ) : (
              <div className="mt-3 text-center">
                <p className="text-sm text-gray-500 mb-3">No sensor statistics computed</p>
                <button
                  onClick={() => handleCompute('sensors', onComputeSensorStats)}
                  disabled={computingSection === 'sensors'}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 mx-auto transition-colors"
                >
                  <Calculator className="w-4 h-4" />
                  {computingSection === 'sensors' ? 'Computing...' : 'Compute Stats'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Standards Results Section */}
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection('standards')}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            {expandedSections.has('standards') ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
            <CheckCircle className="w-5 h-5 text-blue-600" />
            <span className="font-semibold">Standards Compliance</span>
          </div>
          {standardsResults.length > 0 && (
            <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
              {standardsResults.length} standards
            </span>
          )}
        </button>

        {expandedSections.has('standards') && (
          <div className="px-4 pb-4 bg-gray-50">
            {standardsResults.length > 0 ? (
              <div className="space-y-3 mt-3">
                {standardsResults.map((result) => (
                  <div key={result.standardId} className="bg-white rounded p-3 shadow-sm border-l-4 border-blue-500">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-semibold text-gray-800">{result.standardName}</p>
                      {result.status === 'compliant' && <CheckCircle className="w-5 h-5 text-green-500" />}
                      {result.status === 'non_compliant' && <XCircle className="w-5 h-5 text-red-500" />}
                      {result.status === 'warning' && <AlertCircle className="w-5 h-5 text-yellow-500" />}
                    </div>

                    {result.category && (
                      <div className="mb-2">
                        <span className="text-xs font-medium text-gray-500">Category: </span>
                        <span className="text-sm font-bold text-blue-600">{result.category}</span>
                      </div>
                    )}

                    {result.complianceRate !== undefined && (
                      <div className="mb-2">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Compliance Rate</span>
                          <span>{result.complianceRate.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              result.complianceRate >= 75
                                ? 'bg-green-500'
                                : result.complianceRate >= 50
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${result.complianceRate}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {result.violations !== undefined && result.violations > 0 && (
                      <p className="text-xs text-red-600 mb-2">
                        {result.violations} violation{result.violations !== 1 ? 's' : ''} detected
                      </p>
                    )}

                    {result.summary && (
                      <p className="text-xs text-gray-600 mt-2">{result.summary}</p>
                    )}
                  </div>
                ))}

                <button
                  onClick={() => handleCompute('standards', onComputeStandards)}
                  disabled={computingSection === 'standards'}
                  className="w-full mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                >
                  <Calculator className="w-4 h-4" />
                  {computingSection === 'standards' ? 'Computing...' : 'Recompute Standards'}
                </button>
              </div>
            ) : (
              <div className="mt-3 text-center">
                <p className="text-sm text-gray-500 mb-3">No standards results computed</p>
                <button
                  onClick={() => handleCompute('standards', onComputeStandards)}
                  disabled={computingSection === 'standards'}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 mx-auto transition-colors"
                >
                  <Calculator className="w-4 h-4" />
                  {computingSection === 'standards' ? 'Computing...' : 'Compute Standards'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Simulation Results Section */}
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection('simulations')}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            {expandedSections.has('simulations') ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
            <TrendingUp className="w-5 h-5 text-purple-600" />
            <span className="font-semibold">Simulation Results</span>
          </div>
          {simulationResults.length > 0 && (
            <span className="text-sm bg-purple-100 text-purple-800 px-2 py-1 rounded">
              {simulationResults.length} simulations
            </span>
          )}
        </button>

        {expandedSections.has('simulations') && (
          <div className="px-4 pb-4 bg-gray-50">
            {simulationResults.length > 0 ? (
              <div className="space-y-3 mt-3">
                {simulationResults.map((result) => (
                  <div key={result.simulationId} className="bg-white rounded p-3 shadow-sm border-l-4 border-purple-500">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-semibold text-gray-800">{result.simulationName}</p>
                      {result.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-500" />}
                      {result.status === 'failed' && <XCircle className="w-5 h-5 text-red-500" />}
                    </div>

                    {result.summary && (
                      <p className="text-xs text-gray-600 mb-2">{result.summary}</p>
                    )}

                    {result.results && (
                      <div className="mt-2 space-y-1">
                        {Object.entries(result.results).slice(0, 5).map(([key, value]) => (
                          <div key={key} className="text-xs flex justify-between">
                            <span className="text-gray-500">{key}:</span>
                            <span className="text-gray-700 font-medium">
                              {typeof value === 'number' ? value.toFixed(2) : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                <button
                  onClick={() => handleCompute('simulations', onComputeSimulations)}
                  disabled={computingSection === 'simulations'}
                  className="w-full mt-2 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                >
                  <Calculator className="w-4 h-4" />
                  {computingSection === 'simulations' ? 'Computing...' : 'Recompute Simulations'}
                </button>
              </div>
            ) : (
              <div className="mt-3 text-center">
                <p className="text-sm text-gray-500 mb-3">No simulation results available</p>
                <button
                  onClick={() => handleCompute('simulations', onComputeSimulations)}
                  disabled={computingSection === 'simulations'}
                  className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 mx-auto transition-colors"
                >
                  <Calculator className="w-4 h-4" />
                  {computingSection === 'simulations' ? 'Computing...' : 'Compute Simulations'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="px-4 py-4 bg-blue-50 text-xs text-gray-600">
        <p className="font-medium text-gray-700 mb-2">About Statistics:</p>
        <ul className="space-y-1 list-disc list-inside">
          <li>Sensor stats aggregate data from connected sensors</li>
          <li>Standards check compliance with EN16798, BR18, etc.</li>
          <li>Simulations predict occupancy, ventilation needs</li>
          <li>Click compute buttons to calculate or refresh data</li>
        </ul>
      </div>
    </div>
  );
}
