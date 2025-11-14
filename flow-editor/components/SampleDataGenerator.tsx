'use client';

import React from 'react';
import * as Icons from 'lucide-react';

interface SampleDataGeneratorProps {
  onGenerate: (data: any[], fileName: string) => void;
}

export default function SampleDataGenerator({ onGenerate }: SampleDataGeneratorProps) {
  const generateTemperatureData = () => {
    const data = [];
    const startDate = new Date('2024-01-01T00:00:00');

    for (let i = 0; i < 100; i++) {
      const timestamp = new Date(startDate.getTime() + i * 3600000); // Every hour
      data.push({
        timestamp: timestamp.toISOString(),
        temperature: (20 + Math.random() * 5).toFixed(2),
        unit: 'Celsius'
      });
    }

    onGenerate(data, 'sample_temperature_data.csv');
  };

  const generateHumidityData = () => {
    const data = [];
    const startDate = new Date('2024-01-01T00:00:00');

    for (let i = 0; i < 100; i++) {
      const timestamp = new Date(startDate.getTime() + i * 3600000);
      data.push({
        timestamp: timestamp.toISOString(),
        humidity: (40 + Math.random() * 30).toFixed(2),
        unit: '%'
      });
    }

    onGenerate(data, 'sample_humidity_data.csv');
  };

  const generateCO2Data = () => {
    const data = [];
    const startDate = new Date('2024-01-01T00:00:00');

    for (let i = 0; i < 100; i++) {
      const timestamp = new Date(startDate.getTime() + i * 3600000);
      data.push({
        timestamp: timestamp.toISOString(),
        co2: Math.floor(400 + Math.random() * 800),
        unit: 'ppm'
      });
    }

    onGenerate(data, 'sample_co2_data.csv');
  };

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-gray-600 flex items-center gap-1">
        <Icons.Sparkles size={12} />
        Quick Sample Data
      </h4>
      <div className="space-y-1">
        <button
          onClick={generateTemperatureData}
          className="w-full text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
        >
          Temperature Data
        </button>
        <button
          onClick={generateHumidityData}
          className="w-full text-xs px-2 py-1 bg-cyan-100 text-cyan-700 rounded hover:bg-cyan-200 transition-colors"
        >
          Humidity Data
        </button>
        <button
          onClick={generateCO2Data}
          className="w-full text-xs px-2 py-1 bg-slate-100 text-slate-700 rounded hover:bg-slate-200 transition-colors"
        >
          CO2 Data
        </button>
      </div>
    </div>
  );
}
