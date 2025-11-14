'use client';

import React from 'react';
import * as Icons from 'lucide-react';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function HelpModal({ isOpen, onClose }: HelpModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-500 to-purple-500 text-white">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Icons.HelpCircle size={24} />
            Spatial Entity Flow Editor - Quick Guide
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
          >
            <Icons.X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Hierarchy Section */}
          <div className="mb-6">
            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
              <Icons.GitBranch size={20} />
              Typical Hierarchy
            </h3>
            <div className="bg-gray-50 p-4 rounded-lg border-2 border-gray-200">
              <div className="space-y-2 font-mono text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#8B5CF6' }}></div>
                  <span className="font-semibold">Portfolio</span>
                  <span className="text-gray-500">(Top Level)</span>
                </div>
                <div className="flex items-center gap-2 ml-6">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3B82F6' }}></div>
                  <span className="font-semibold">└── Building(s)</span>
                </div>
                <div className="flex items-center gap-2 ml-12">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10B981' }}></div>
                  <span className="font-semibold">└── Floor(s)</span>
                </div>
                <div className="flex items-center gap-2 ml-18">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#F59E0B' }}></div>
                  <span className="font-semibold">└── Room(s)</span>
                </div>
                <div className="flex items-center gap-2 ml-24">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EF4444' }}></div>
                  <span>└── Sensor(s)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Start */}
          <div className="mb-6">
            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
              <Icons.Zap size={20} />
              Quick Start
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                <div className="font-semibold text-blue-900 mb-1 flex items-center gap-2">
                  <Icons.MousePointer2 size={16} />
                  Add Nodes
                </div>
                <p className="text-sm text-blue-800">
                  Drag components from the right panel onto the canvas
                </p>
              </div>

              <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                <div className="font-semibold text-green-900 mb-1 flex items-center gap-2">
                  <Icons.GitBranchPlus size={16} />
                  Connect Nodes
                </div>
                <p className="text-sm text-green-800">
                  Drag from bottom handle (●) to top handle (●) of another node
                </p>
              </div>

              <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                <div className="font-semibold text-purple-900 mb-1 flex items-center gap-2">
                  <Icons.Upload size={16} />
                  Upload Data
                </div>
                <p className="text-sm text-purple-800">
                  Click sensor nodes and use CSV upload or sample data
                </p>
              </div>

              <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
                <div className="font-semibold text-orange-900 mb-1 flex items-center gap-2">
                  <Icons.Download size={16} />
                  Export Graph
                </div>
                <p className="text-sm text-orange-800">
                  Use Export button to save your structure as JSON
                </p>
              </div>
            </div>
          </div>

          {/* Node Types */}
          <div className="mb-6">
            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
              <Icons.Layers size={20} />
              Available Node Types
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {/* Spatial */}
              <div className="space-y-2">
                <h4 className="font-semibold text-sm text-gray-600">Spatial Entities</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: '#8B5CF6' }}></div>
                    <span>Portfolio</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: '#3B82F6' }}></div>
                    <span>Building</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: '#10B981' }}></div>
                    <span>Floor</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: '#F59E0B' }}></div>
                    <span>Room</span>
                  </div>
                </div>
              </div>

              {/* Sensors */}
              <div className="space-y-2">
                <h4 className="font-semibold text-sm text-gray-600">Sensors</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EF4444' }}></div>
                    <span>Temperature</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#06B6D4' }}></div>
                    <span>Humidity</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#64748B' }}></div>
                    <span>CO2</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#8B5CF6' }}></div>
                    <span>Occupancy</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#FBBF24' }}></div>
                    <span>Light</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#22C55E' }}></div>
                    <span>Energy</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-yellow-50 p-4 rounded-lg border-2 border-yellow-200">
            <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-yellow-900">
              <Icons.Lightbulb size={18} />
              Pro Tips
            </h3>
            <ul className="space-y-1 text-sm text-yellow-900">
              <li>• Use the mouse wheel to zoom in and out</li>
              <li>• Click and drag the background to pan around</li>
              <li>• Select a node to see details and upload CSV data</li>
              <li>• Use sample data generators for quick testing</li>
              <li>• Export your work regularly to save progress</li>
              <li>• Delete nodes by selecting them and clicking the trash icon</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
}
