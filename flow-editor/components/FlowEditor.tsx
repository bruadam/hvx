'use client';

import React, { useState, useCallback, useRef } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  Panel,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';
import * as Icons from 'lucide-react';

import CustomNode from './CustomNode';
import NodeLibrary from './NodeLibrary';
import CSVUploadModal from './CSVUploadModal';
import CSVColumnMapper from './CSVColumnMapper';
import ZipFlowGenerator from './ZipFlowGenerator';
import SampleDataGenerator from './SampleDataGenerator';
import HelpModal from './HelpModal';
import NodePropertiesModal from './NodePropertiesModal';
import StatisticsPanel from './StatisticsPanel';
import { BaseNodeType, NodeData, SpatialEntityType, SensorType, MetricMapping, getNodeConfig } from '@/lib/nodeTypes';
import {
  computeSensorStatistics,
  computeStandardsCompliance,
  computeSimulations,
  computeAllStatistics,
} from '@/lib/statisticsUtils';

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

let nodeId = 0;
const getId = () => `node_${nodeId++}`;

export default function FlowEditor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isCSVModalOpen, setIsCSVModalOpen] = useState(false);
  const [isColumnMapperOpen, setIsColumnMapperOpen] = useState(false);
  const [isZipGeneratorOpen, setIsZipGeneratorOpen] = useState(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const [isPropertiesModalOpen, setIsPropertiesModalOpen] = useState(false);
  const [showSensors, setShowSensors] = useState(true);
  const [pendingCSVData, setPendingCSVData] = useState<{data: any[], fileName: string} | null>(null);
  const [showStatistics, setShowStatistics] = useState(false);
  const [statisticsNode, setStatisticsNode] = useState<Node<NodeData> | null>(null);

  const onConnect = useCallback(
    (params: Connection) => {
      if (!params.source || !params.target) return;

      // Find source and target nodes
      const sourceNode = nodes.find((n) => n.id === params.source);
      const targetNode = nodes.find((n) => n.id === params.target);

      if (!sourceNode || !targetNode) return;

      // Determine edge style based on node types
      // NEW LOGIC: Edges flow FROM spatial entities TO sensors
      const sourceIsSensor = sourceNode.data.baseType === 'sensor';
      const targetIsSensor = targetNode.data.baseType === 'sensor';

      let edgeStyle: any;
      let animated = false;

      if (!sourceIsSensor && targetIsSensor) {
        // Spatial entity to sensor - colored and animated (main direction)
        const sensorConfig = getNodeConfig(targetNode.data);
        edgeStyle = { stroke: sensorConfig.color, strokeWidth: 2 };
        animated = true;
      } else if (sourceIsSensor && !targetIsSensor) {
        // Sensor to spatial entity - also allowed, colored and animated
        const sensorConfig = getNodeConfig(sourceNode.data);
        edgeStyle = { stroke: sensorConfig.color, strokeWidth: 2 };
        animated = true;
      } else {
        // Both spatial entities or both sensors - static grey
        edgeStyle = { stroke: '#9CA3AF', strokeWidth: 2 };
        animated = false;
      }

      setEdges((eds) =>
        addEdge(
          {
            ...params,
            animated,
            style: edgeStyle,
          },
          eds
        )
      );
    },
    [setEdges, nodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const baseType = event.dataTransfer.getData('application/reactflow') as BaseNodeType;
      if (!baseType || !reactFlowInstance) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      // Set default subType based on baseType
      const defaultSubType: SpatialEntityType | SensorType =
        baseType === 'spatialEntity' ? 'room' : 'indoor_climate';

      const newNode: Node<NodeData> = {
        id: getId(),
        type: 'custom',
        position,
        data: {
          label: `${baseType === 'spatialEntity' ? 'Spatial Entity' : 'Sensor'} ${nodeId}`,
          baseType: baseType,
          subType: defaultSubType,
          metadata: {
            name: `${baseType === 'spatialEntity' ? 'Spatial Entity' : 'Sensor'} ${nodeId}`,
          },
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onNodeDoubleClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setIsPropertiesModalOpen(true);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleDragStart = (event: React.DragEvent, baseType: BaseNodeType) => {
    event.dataTransfer.setData('application/reactflow', baseType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const updateEdgeStyles = useCallback((updatedNodes: Node<NodeData>[]) => {
    setEdges((currentEdges) =>
      currentEdges.map((edge) => {
        const sourceNode = updatedNodes.find((n) => n.id === edge.source);
        const targetNode = updatedNodes.find((n) => n.id === edge.target);

        if (!sourceNode || !targetNode) return edge;

        const sourceIsSensor = sourceNode.data.baseType === 'sensor';
        const targetIsSensor = targetNode.data.baseType === 'sensor';

        let edgeStyle: any;
        let animated = false;

        if (!sourceIsSensor && targetIsSensor) {
          // Spatial entity to sensor - colored and animated (main direction)
          const sensorConfig = getNodeConfig(targetNode.data);
          edgeStyle = { stroke: sensorConfig.color, strokeWidth: 2 };
          animated = true;
        } else if (sourceIsSensor && !targetIsSensor) {
          // Sensor to spatial entity - also allowed, colored and animated
          const sensorConfig = getNodeConfig(sourceNode.data);
          edgeStyle = { stroke: sensorConfig.color, strokeWidth: 2 };
          animated = true;
        } else {
          // Both spatial entities or both sensors - static grey
          edgeStyle = { stroke: '#9CA3AF', strokeWidth: 2 };
          animated = false;
        }

        return {
          ...edge,
          animated,
          style: edgeStyle,
        };
      })
    );
  }, [setEdges]);

  const handleNodePropertiesUpdate = (updatedData: Partial<NodeData>) => {
    if (!selectedNode) return;

    const updatedNodes = nodes.map((node) => {
      if (node.id === selectedNode.id) {
        return {
          ...node,
          data: {
            ...node.data,
            ...updatedData,
          },
        };
      }
      return node;
    });

    setNodes(updatedNodes);

    // Update edge styles if the node type changed
    if (updatedData.baseType || updatedData.subType) {
      updateEdgeStyles(updatedNodes);
    }
  };

  const handleCSVUpload = (data: any[], fileName: string) => {
    if (!selectedNode) return;

    // Store CSV data temporarily and open column mapper
    setPendingCSVData({ data, fileName });
    setIsCSVModalOpen(false);
    setIsColumnMapperOpen(true);
  };

  const handleMetricMappingsSave = (mappings: MetricMapping[]) => {
    if (!selectedNode || !pendingCSVData) return;

    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === selectedNode.id) {
          return {
            ...node,
            data: {
              ...node.data,
              csvData: pendingCSVData.data,
              csvFile: pendingCSVData.fileName,
              metadata: {
                ...node.data.metadata,
                metricMappings: mappings,
              },
            },
          };
        }
        return node;
      })
    );

    setPendingCSVData(null);
  };

  const handleDeleteNode = () => {
    if (!selectedNode) return;

    setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
    setEdges((eds) =>
      eds.filter(
        (edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id
      )
    );
    setSelectedNode(null);
  };

  const handleExportJSON = () => {
    const data = {
      nodes: nodes.map((node) => ({
        id: node.id,
        baseType: node.data.baseType,
        subType: node.data.subType,
        label: node.data.label,
        metadata: node.data.metadata,
        position: node.position,
        csvFile: node.data.csvFile,
        recordCount: node.data.csvData?.length || 0,
      })),
      edges: edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
      })),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'spatial-entity-graph.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClearAll = () => {
    if (confirm('Are you sure you want to clear all nodes and connections?')) {
      setNodes([]);
      setEdges([]);
      setSelectedNode(null);
    }
  };

  const handleZipFlowGenerate = (newNodes: Node<NodeData>[], newEdges: Edge[]) => {
    setNodes(newNodes);
    setEdges(newEdges);
  };

  const handleShowStatistics = (node: Node<NodeData>) => {
    setStatisticsNode(node);
    setShowStatistics(true);
  };

  const handleComputeSensorStats = async () => {
    if (!statisticsNode) return;

    const stats = computeSensorStatistics(statisticsNode, nodes, edges);

    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === statisticsNode.id) {
          return {
            ...node,
            data: {
              ...node.data,
              statistics: {
                ...node.data.statistics,
                sensorStats: stats,
                lastComputedAt: new Date().toISOString(),
              },
            },
          };
        }
        return node;
      })
    );

    // Update statistics node state
    setStatisticsNode((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        data: {
          ...prev.data,
          statistics: {
            ...prev.data.statistics,
            sensorStats: stats,
            lastComputedAt: new Date().toISOString(),
          },
        },
      };
    });
  };

  const handleComputeStandards = async () => {
    if (!statisticsNode) return;

    const standards = await computeStandardsCompliance(statisticsNode, nodes, edges);

    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === statisticsNode.id) {
          return {
            ...node,
            data: {
              ...node.data,
              statistics: {
                ...node.data.statistics,
                standardsResults: standards,
                lastComputedAt: new Date().toISOString(),
              },
            },
          };
        }
        return node;
      })
    );

    // Update statistics node state
    setStatisticsNode((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        data: {
          ...prev.data,
          statistics: {
            ...prev.data.statistics,
            standardsResults: standards,
            lastComputedAt: new Date().toISOString(),
          },
        },
      };
    });
  };

  const handleComputeSimulations = async () => {
    if (!statisticsNode) return;

    const simulations = await computeSimulations(statisticsNode, nodes, edges);

    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === statisticsNode.id) {
          return {
            ...node,
            data: {
              ...node.data,
              statistics: {
                ...node.data.statistics,
                simulationResults: simulations,
                lastComputedAt: new Date().toISOString(),
              },
            },
          };
        }
        return node;
      })
    );

    // Update statistics node state
    setStatisticsNode((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        data: {
          ...prev.data,
          statistics: {
            ...prev.data.statistics,
            simulationResults: simulations,
            lastComputedAt: new Date().toISOString(),
          },
        },
      };
    });
  };

  const isSensorNode = selectedNode?.data.baseType === 'sensor';
  const isSpatialEntityNode = selectedNode?.data.baseType === 'spatialEntity';

  // Filter nodes based on sensor visibility
  const visibleNodes = showSensors
    ? nodes
    : nodes.filter(node => node.data.baseType !== 'sensor');

  // Filter edges to only show edges connected to visible nodes
  const visibleEdges = showSensors
    ? edges
    : edges.filter(edge => {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        return sourceNode?.data.baseType !== 'sensor' && targetNode?.data.baseType !== 'sensor';
      });

  return (
    <div className="flex h-screen">
      <div className="flex-1 relative" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={visibleNodes}
          edges={visibleEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          fitView
          className="bg-gray-50"
        >
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          <Controls />

          {/* Top Panel - Toolbar */}
          <Panel position="top-left" className="bg-white rounded-lg shadow-lg p-2 flex gap-2">
            <button
              onClick={() => setIsHelpModalOpen(true)}
              className="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
              title="Help"
            >
              <Icons.HelpCircle size={16} />
              Help
            </button>
            <button
              onClick={() => setIsZipGeneratorOpen(true)}
              className="flex items-center gap-2 px-3 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
              title="Upload Portfolio Zip"
            >
              <Icons.FolderArchive size={16} />
              Import Zip
            </button>
            <button
              onClick={() => setShowSensors(!showSensors)}
              className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
                showSensors
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-gray-300 hover:bg-gray-400 text-gray-700'
              }`}
              title={showSensors ? 'Hide Sensors' : 'Show Sensors'}
            >
              {showSensors ? <Icons.Eye size={16} /> : <Icons.EyeOff size={16} />}
              Sensors
            </button>
            <button
              onClick={handleExportJSON}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              title="Export to JSON"
            >
              <Icons.Download size={16} />
              Export
            </button>
            <button
              onClick={handleClearAll}
              className="flex items-center gap-2 px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              title="Clear all"
            >
              <Icons.Trash2 size={16} />
              Clear
            </button>
          </Panel>

          {/* Node Info Panel */}
          {selectedNode && (
            <Panel position="top-right" className="bg-white rounded-lg shadow-lg p-4 min-w-[250px]">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-lg">Node Details</h3>
                <button
                  onClick={handleDeleteNode}
                  className="p-1 hover:bg-red-100 rounded-full transition-colors text-red-600"
                  title="Delete node"
                >
                  <Icons.Trash2 size={18} />
                </button>
              </div>

              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-semibold">Type:</span>{' '}
                  {getNodeConfig(selectedNode.data).label}
                </div>
                <div>
                  <span className="font-semibold">Label:</span> {selectedNode.data.label}
                </div>
                <div>
                  <span className="font-semibold">ID:</span> {selectedNode.id}
                </div>

                {selectedNode.data.csvFile && (
                  <>
                    <div>
                      <span className="font-semibold">CSV File:</span>{' '}
                      {selectedNode.data.csvFile}
                    </div>
                    <div>
                      <span className="font-semibold">Records:</span>{' '}
                      {selectedNode.data.csvData?.length || 0}
                    </div>
                  </>
                )}
              </div>

              <button
                onClick={() => setIsPropertiesModalOpen(true)}
                className="mt-4 w-full flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <Icons.Settings size={16} />
                Edit Properties
              </button>

              {isSpatialEntityNode && (
                <button
                  onClick={() => handleShowStatistics(selectedNode)}
                  className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                >
                  <Icons.BarChart3 size={16} />
                  View Statistics
                </button>
              )}

              {isSensorNode && (
                <>
                  <button
                    onClick={() => setIsCSVModalOpen(true)}
                    className="mt-4 w-full flex items-center justify-center gap-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                  >
                    <Icons.Upload size={16} />
                    {selectedNode.data.csvFile ? 'Update CSV' : 'Upload CSV'}
                  </button>

                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <SampleDataGenerator onGenerate={handleCSVUpload} />
                  </div>
                </>
              )}
            </Panel>
          )}
        </ReactFlow>
      </div>

      <NodeLibrary onDragStart={handleDragStart} />

      <CSVUploadModal
        isOpen={isCSVModalOpen}
        onClose={() => setIsCSVModalOpen(false)}
        onUpload={handleCSVUpload}
        nodeLabel={selectedNode?.data.label || ''}
      />

      <HelpModal
        isOpen={isHelpModalOpen}
        onClose={() => setIsHelpModalOpen(false)}
      />

      {selectedNode && (
        <NodePropertiesModal
          isOpen={isPropertiesModalOpen}
          onClose={() => setIsPropertiesModalOpen(false)}
          nodeData={selectedNode.data}
          onSave={handleNodePropertiesUpdate}
        />
      )}

      {pendingCSVData && (
        <CSVColumnMapper
          isOpen={isColumnMapperOpen}
          onClose={() => {
            setIsColumnMapperOpen(false);
            setPendingCSVData(null);
          }}
          csvData={pendingCSVData.data}
          currentMappings={selectedNode?.data.metadata?.metricMappings || []}
          onSave={handleMetricMappingsSave}
        />
      )}

      <ZipFlowGenerator
        isOpen={isZipGeneratorOpen}
        onClose={() => setIsZipGeneratorOpen(false)}
        onGenerate={handleZipFlowGenerate}
      />

      {showStatistics && statisticsNode && (
        <div className="fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-30"
            onClick={() => setShowStatistics(false)}
          />
          {/* Statistics Panel */}
          <div className="relative ml-auto h-full">
            <StatisticsPanel
              nodeId={statisticsNode.id}
              nodeLabel={statisticsNode.data.label}
              nodeType={statisticsNode.data.subType as 'portfolio' | 'building' | 'floor' | 'room'}
              statistics={statisticsNode.data.statistics}
              onComputeSensorStats={handleComputeSensorStats}
              onComputeStandards={handleComputeStandards}
              onComputeSimulations={handleComputeSimulations}
            />
            {/* Close button */}
            <button
              onClick={() => setShowStatistics(false)}
              className="absolute top-4 left-4 z-10 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100 transition-colors"
              title="Close statistics"
            >
              <Icons.X size={20} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
