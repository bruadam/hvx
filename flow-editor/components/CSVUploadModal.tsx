'use client';

import React, { useState, useRef } from 'react';
import * as Icons from 'lucide-react';
import Papa from 'papaparse';

interface CSVUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (data: any[], fileName: string) => void;
  nodeLabel: string;
}

export default function CSVUploadModal({
  isOpen,
  onClose,
  onUpload,
  nodeLabel,
}: CSVUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }

    setFile(selectedFile);
    setError(null);

    Papa.parse(selectedFile, {
      header: true,
      preview: 5,
      complete: (results) => {
        setPreview(results.data);
      },
      error: (err) => {
        setError(err.message);
      },
    });
  };

  const handleUpload = () => {
    if (!file) return;

    Papa.parse(file, {
      header: true,
      complete: (results) => {
        onUpload(results.data, file.name);
        handleClose();
      },
      error: (err) => {
        setError(err.message);
      },
    });
  };

  const handleClose = () => {
    setFile(null);
    setPreview(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Icons.Upload size={20} />
            Upload CSV Data for {nodeLabel}
          </h2>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Icons.X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {/* File Input */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            <Icons.FileSpreadsheet size={48} className="mx-auto text-gray-400 mb-2" />
            <p className="text-gray-600 mb-1">
              {file ? file.name : 'Click to select CSV file'}
            </p>
            <p className="text-sm text-gray-400">or drag and drop</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-start gap-2">
              <Icons.AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Preview */}
          {preview && preview.length > 0 && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <Icons.Eye size={16} />
                Preview (first 5 rows)
              </h3>
              <div className="overflow-x-auto border rounded-lg">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(preview[0]).map((header) => (
                        <th
                          key={header}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {preview.map((row, idx) => (
                      <tr key={idx}>
                        {Object.values(row).map((cell: any, cellIdx) => (
                          <td
                            key={cellIdx}
                            className="px-4 py-2 whitespace-nowrap text-gray-700"
                          >
                            {cell?.toString() || '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t bg-gray-50">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Icons.Check size={16} />
            Upload
          </button>
        </div>
      </div>
    </div>
  );
}
