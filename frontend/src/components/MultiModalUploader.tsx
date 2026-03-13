import React, { useState, useCallback } from 'react';
import { Upload, CheckCircle, AlertCircle, XCircle } from 'lucide-react';

interface ImagePreview {
  file: File;
  preview: string;
  quality?: 'high' | 'medium' | 'low';
}

interface UploadStatus {
  fundus?: ImagePreview;
  oct?: ImagePreview;
  processing?: boolean;
  error?: string;
}

/**
 * Multi-Modal Uploader Component (Week 1 - P0.1/P0.2)
 * 
 * Allows clinical users to upload paired Fundus + OCT images
 * with real-time preview and quality assessment feedback.
 */
export const MultiModalUploader: React.FC = () => {
  const [uploads, setUploads] = useState<UploadStatus>({});
  const [analyzing, setAnalyzing] = useState(false);
  const [clinicalData, setClinicalData] = useState({
    age: 50,
    iop: 15,
    diabetes_status: 'No',
    gender: 'Male',
    spherical_equivalent: 0.0
  });

  const handleFileSelect = useCallback((type: 'fundus' | 'oct', file: File) => {
    if (!file.type.includes('image')) {
      setUploads(prev => ({ ...prev, error: 'Please select an image file' }));
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = e.target?.result as string;
      setUploads(prev => ({
        ...prev,
        [type]: { file, preview },
        error: undefined
      }));
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = (type: 'fundus' | 'oct') => (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(type, file);
  };

  const handleAnalyze = async () => {
    if (!uploads.fundus || !uploads.oct) {
      setUploads(prev => ({ ...prev, error: 'Please upload both images' }));
      return;
    }

    setAnalyzing(true);
    const formData = new FormData();
    formData.append('fundus', uploads.fundus.file);
    formData.append('oct', uploads.oct.file);
    
    // Append clinical data properly formatted as JSON string
    formData.append('metadata', JSON.stringify({ clinical_data: clinicalData }));

    try {
      const response = await fetch('/api/ml/analyze/mtl', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        // Redirect to results page or show results
        console.log('Analysis complete:', result);
      } else {
        setUploads(prev => ({ ...prev, error: 'Analysis failed' }));
      }
    } catch (error) {
      setUploads(prev => ({ ...prev, error: 'Network error' }));
    } finally {
      setAnalyzing(false);
    }
  };

  const renderUploadBox = (type: 'fundus' | 'oct', label: string) => {
    const image = uploads[type];
    const inputId = `${type}-input`;

    return (
      <div className="w-full sm:flex-1 border-2 border-dashed border-blue-300 rounded-lg p-6 text-center bg-blue-50 hover:bg-blue-100 transition" onDrop={handleDrop(type)} onDragOver={(e) => e.preventDefault()}>
        <input
          id={inputId}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => e.target.files?.[0] && handleFileSelect(type, e.target.files[0])}
        />
        
        {image ? (
          <div className="space-y-2">
            <img src={image.preview} alt={label} className="w-32 h-32 object-cover mx-auto rounded" />
            <p className="text-sm font-medium text-gray-700">{label} ✓</p>
            <button onClick={() => setUploads(prev => ({ ...prev, [type]: undefined }))} className="text-s text-red-600 hover:underline">
              Remove
            </button>
          </div>
        ) : (
          <div>
            <Upload size={32} className="mx-auto text-blue-600 mb-2" />
            <label htmlFor={inputId} className="cursor-pointer">
              <span className="text-blue-600 hover:underline font-medium">Click to upload</span>
              <span className="text-gray-500"> or drag {label.toLowerCase()}</span>
            </label>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Upload className="text-blue-600" />
        Multi-Modal Image Analysis
      </h2>

      {/* Upload boxes */}
      <div className="flex flex-col sm:flex-row gap-6 mb-6">
        {renderUploadBox('fundus', 'Fundus Image')}
        {renderUploadBox('oct', 'OCT Image')}
      </div>

      {/* Error message */}
      {uploads.error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-red-700 flex items-center gap-2">
          <XCircle size={18} />
          {uploads.error}
        </div>
      )}

      {/* Clinical Metadata Inputs */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-700">Clinical Metadata (Optional)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
            <input 
              type="number" 
              value={clinicalData.age}
              onChange={(e) => setClinicalData({...clinicalData, age: Number(e.target.value)})}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">IOP (mmHg)</label>
            <input 
              type="number" 
              value={clinicalData.iop}
              step="0.1"
              onChange={(e) => setClinicalData({...clinicalData, iop: Number(e.target.value)})}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Spherical Equivalent</label>
            <input 
              type="number" 
              value={clinicalData.spherical_equivalent}
              step="0.25"
              onChange={(e) => setClinicalData({...clinicalData, spherical_equivalent: Number(e.target.value)})}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Diabetes Status</label>
            <select 
              value={clinicalData.diabetes_status}
              onChange={(e) => setClinicalData({...clinicalData, diabetes_status: e.target.value})}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
            <select 
              value={clinicalData.gender}
              onChange={(e) => setClinicalData({...clinicalData, gender: e.target.value})}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
      </div>

      {/* Analyze button */}
      <button
        onClick={handleAnalyze}
        disabled={!uploads.fundus || !uploads.oct || analyzing}
        className="w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition"
      >
        {analyzing ? 'Analyzing...' : 'Analyze Hybrid Data'}
      </button>

      {/* Help text */}
      <p className="mt-4 text-sm text-gray-500 text-center">
        Both Fundus and OCT images are required for multi-modal analysis (H1 hypothesis validation)
      </p>
    </div>
  );
};
