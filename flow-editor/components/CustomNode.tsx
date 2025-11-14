'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import * as Icons from 'lucide-react';
import { NodeData, getNodeConfig } from '@/lib/nodeTypes';

const CustomNode = memo(({ data, selected }: NodeProps<NodeData>) => {
  const config = getNodeConfig(data);
  const IconComponent = Icons[config.icon as keyof typeof Icons] as React.ComponentType<any>;

  return (
    <div
      className={`px-4 py-3 shadow-lg rounded-lg border-2 min-w-[150px] transition-all ${
        selected ? 'ring-2 ring-offset-2 ring-blue-500' : ''
      }`}
      style={{
        backgroundColor: config.color + '20',
        borderColor: config.color,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3"
        style={{ background: config.color }}
      />

      <div className="flex items-center gap-2">
        {IconComponent && (
          <div
            className="p-2 rounded-md"
            style={{ backgroundColor: config.color + '40' }}
          >
            <IconComponent size={20} style={{ color: config.color }} />
          </div>
        )}
        <div className="flex flex-col">
          <div className="text-xs font-semibold text-gray-600">
            {config.label}
          </div>
          <div className="text-sm font-bold" style={{ color: config.color }}>
            {data.label}
          </div>
        </div>
      </div>

      {/* Display metadata preview */}
      {data.metadata && (
        <div className="mt-2 text-xs text-gray-500 space-y-1">
          {data.baseType === 'spatialEntity' && data.metadata.area && (
            <div className="flex items-center gap-1">
              <Icons.Square size={10} />
              <span>{data.metadata.area} m²</span>
            </div>
          )}
          {data.baseType === 'sensor' && data.metadata.metricMappings && data.metadata.metricMappings.length > 0 && (
            <div className="flex items-center gap-1">
              <Icons.MapPin size={10} />
              <span>{data.metadata.metricMappings.length} metric{data.metadata.metricMappings.length !== 1 ? 's' : ''}</span>
            </div>
          )}
          {data.baseType === 'sensor' && data.metadata.unit && !data.metadata.metricMappings && (
            <div className="flex items-center gap-1">
              <Icons.Ruler size={10} />
              <span>Unit: {data.metadata.unit}</span>
            </div>
          )}
        </div>
      )}

      {data.csvFile && (
        <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
          <Icons.FileSpreadsheet size={12} />
          <span className="truncate max-w-[120px]" title={data.csvFile}>
            {data.csvFile}
          </span>
        </div>
      )}

      {data.csvData && data.csvData.length > 0 && (
        <div className="mt-1 text-xs text-gray-600">
          {data.csvData.length} records
        </div>
      )}

      {/* Statistics indicator for spatial entities */}
      {data.baseType === 'spatialEntity' && data.statistics && (
        <div className="mt-2 pt-2 border-t border-gray-300">
          <div className="flex items-center gap-2 text-xs">
            {data.statistics.sensorStats && (
              <div className="flex items-center gap-1 text-green-600" title="Sensor stats computed">
                <Icons.Activity size={12} />
                <span>{data.statistics.sensorStats.sensorCount}</span>
              </div>
            )}
            {data.statistics.standardsResults && data.statistics.standardsResults.length > 0 && (
              <div className="flex items-center gap-1 text-blue-600" title="Standards computed">
                <Icons.CheckCircle size={12} />
                <span>{data.statistics.standardsResults.length}</span>
              </div>
            )}
            {data.statistics.simulationResults && data.statistics.simulationResults.length > 0 && (
              <div className="flex items-center gap-1 text-purple-600" title="Simulations computed">
                <Icons.TrendingUp size={12} />
                <span>{data.statistics.simulationResults.length}</span>
              </div>
            )}
          </div>
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3"
        style={{ background: config.color }}
      />
    </div>
  );
});

CustomNode.displayName = 'CustomNode';

export default CustomNode;
