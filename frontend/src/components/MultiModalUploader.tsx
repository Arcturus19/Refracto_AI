import React, { useState, useCallback } from 'react';
import { Upload, CheckCircle, AlertCircle, XCircle, Loader2 } from 'lucide-react';
import { generateDicomPreview } from '../utils/dicomParser';

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
    const isImage = file.type.startsWith('image/');
    const isDicom = file.name.toLowerCase().endsWith('.dcm') || file.name.toLowerCase().endsWith('.dicom');

    if (!isImage && !isDicom) {
      setUploads(prev => ({ ...prev, error: 'Please select an image or DICOM file' }));
      return;
    }

    setUploads(prev => ({ ...prev, processing: true, error: undefined }));

    if (isDicom) {
      generateDicomPreview(file)
        .then(preview => {
          setUploads(prev => ({
            ...prev,
            [type]: { file, preview },
            processing: false
          }));
        })
        .catch(err => {
          console.error("DICOM preview generation failed:", err);
          setUploads(prev => ({
             ...prev, 
             processing: false, 
             error: 'Failed to generate DICOM preview' 
          }));
        });
    } else {
      const reader = new FileReader();
      reader.onload = (e) => {
        const preview = e.target?.result as string;
        setUploads(prev => ({
          ...prev,
          [type]: { file, preview },
          processing: false
        }));
      };
      reader.readAsDataURL(file);
    }
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
      <div 
        className={`w-full sm:flex-1 border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300 group
          ${image ? 'border-sky-300 bg-sky-50/50' : 'border-slate-300 bg-slate-50 hover:bg-sky-50 hover:border-sky-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-sky-100'}
        `}
        onDrop={handleDrop(type)} 
        onDragOver={(e) => e.preventDefault()}
      >
        <input
          id={inputId}
          type="file"
          accept="image/*,.dcm,.dicom"
          hidden
          onChange={(e) => e.target.files?.[0] && handleFileSelect(type, e.target.files[0])}
        />
        
        {image ? (
          <div className="space-y-3 animate-fade-in relative">
            <div className="relative inline-block">
              <img src={image.preview} alt={label} className="w-32 h-32 object-cover mx-auto rounded-xl shadow-sm border border-slate-200" />
              <button 
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setUploads(prev => ({ ...prev, [type]: undefined })) }} 
                className="absolute -top-2 -right-2 bg-white text-rose-500 rounded-full p-1 shadow-md hover:bg-rose-50 transition-colors"
                title="Remove image"
              >
                <XCircle size={18} />
              </button>
            </div>
            <p className="text-sm font-semibold text-slate-700 flex items-center justify-center gap-1">
              {label} <CheckCircle size={14} className="text-emerald-500" />
            </p>
          </div>
        ) : uploads.processing && !uploads[type] ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[140px] text-sky-500">
             <Loader2 size={32} className="animate-spin mb-3" />
             <span className="text-sm">Processing...</span>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full min-h-[140px]">
            <div className="p-4 bg-white rounded-full shadow-sm mb-4 group-hover:scale-110 group-hover:bg-sky-100 transition-all duration-300">
              <Upload size={28} className="text-sky-500" />
            </div>
            <label htmlFor={inputId} className="cursor-pointer flex flex-col items-center">
              <span className="text-sky-600 hover:text-sky-700 font-semibold mb-1">Click to upload</span>
              <span className="text-slate-500 text-sm">or drag {label.toLowerCase()}</span>
            </label>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-8 bg-white rounded-3xl premium-shadow">
      <h2 className="text-2xl font-bold mb-8 flex items-center gap-3 text-slate-800">
        <div className="p-2.5 bg-sky-50 text-sky-600 rounded-xl">
          <Upload size={24} />
        </div>
        Multi-Modal Image Analysis
      </h2>

      {/* Upload boxes */}
      <div className="flex flex-col sm:flex-row gap-6 mb-8">
        {renderUploadBox('fundus', 'Fundus Image')}
        {renderUploadBox('oct', 'OCT Image')}
      </div>

      {/* Error message */}
      {uploads.error && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-100 rounded-2xl text-rose-700 flex items-center gap-3 animate-fade-in shadow-sm">
          <AlertCircle size={20} className="text-rose-500 flex-shrink-0" />
          <span className="font-medium">{uploads.error}</span>
        </div>
      )}

      {/* Clinical Metadata Inputs */}
      <div className="mb-8 p-6 bg-slate-50/80 rounded-2xl border border-slate-100/80">
        <h3 className="text-lg font-semibold mb-5 text-slate-800 flex items-center gap-2">
          Clinical Metadata 
          <span className="text-xs font-normal text-slate-500 bg-slate-200/50 px-2 py-0.5 rounded-full">Optional</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Age</label>
            <input 
              type="number" 
              value={clinicalData.age}
              onChange={(e) => setClinicalData({...clinicalData, age: Number(e.target.value)})}
              className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all outline-none text-slate-800"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">IOP (mmHg)</label>
            <input 
              type="number" 
              value={clinicalData.iop}
              step="0.1"
              onChange={(e) => setClinicalData({...clinicalData, iop: Number(e.target.value)})}
              className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all outline-none text-slate-800"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Spherical Eq</label>
            <input 
              type="number" 
              value={clinicalData.spherical_equivalent}
              step="0.25"
              onChange={(e) => setClinicalData({...clinicalData, spherical_equivalent: Number(e.target.value)})}
              className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all outline-none text-slate-800"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Diabetes Status</label>
            <select 
              value={clinicalData.diabetes_status}
              onChange={(e) => setClinicalData({...clinicalData, diabetes_status: e.target.value})}
              className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all outline-none text-slate-800"
            >
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Gender</label>
            <select 
              value={clinicalData.gender}
              onChange={(e) => setClinicalData({...clinicalData, gender: e.target.value})}
              className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-sky-500/10 focus:border-sky-500 transition-all outline-none text-slate-800"
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
        className="w-full bg-sky-600 text-white py-4 rounded-xl hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 font-semibold text-lg transition-all duration-300 hover:-translate-y-1 shadow-lg shadow-sky-600/20 active:scale-[0.98]"
      >
        {analyzing ? 'Analyzing Multi-Modal Data...' : 'Analyze Hybrid Data'}
      </button>

      {/* Help text */}
      <p className="mt-4 text-sm text-gray-500 text-center">
        Both Fundus and OCT images are required for multi-modal analysis (H1 hypothesis validation)
      </p>
    </div>
  );
};
