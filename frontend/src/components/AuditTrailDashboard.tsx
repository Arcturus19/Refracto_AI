import React, { useState, useEffect } from 'react';
import { FileText, Download, Filter, Calendar } from 'lucide-react';

interface AuditLogEntry {
  log_id: string;
  timestamp: string;
  anonymized_patient_hash: string;
  model_version: string;
  task: 'DR' | 'Glaucoma' | 'Refraction';
  prediction: string;
  confidence: number;
  correction_applied: boolean;
  correction_factor?: number;
  consent_verified: boolean;
  ethics_approval_id: string;
  clinician_feedback?: {
    clinician_id: string;
    clinician_agreement: number;
    clinician_feedback: string;
    feedback_timestamp: string;
  };
}

interface AuditTrailDashboardProps {
  patientHash?: string;
  dateRange?: { start: string; end: string };
  onExportCompliance?: () => void;
}

/**
 * Audit Trail Dashboard (Week 1 - P0.6)
 * 
 * Displays immutable prediction audit logs with:
 * - Append-only design (predictions cannot be deleted/modified)
 * - Clinician feedback tracking (added separately)
 * - Compliance export (no PII)
 * - Immutability verification
 * 
 * Satisfies ethics requirements for clinical decision support systems.
 */
export const AuditTrailDashboard: React.FC<AuditTrailDashboardProps> = ({
  patientHash,
  dateRange,
  onExportCompliance
}) => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterTask, setFilterTask] = useState<'All' | 'DR' | 'Glaucoma' | 'Refraction'>('All');

  useEffect(() => {
    fetchAuditLogs();
  }, [patientHash, dateRange]);

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (patientHash) params.append('patient_hash', patientHash);
      if (dateRange) {
        params.append('start_date', dateRange.start);
        params.append('end_date', dateRange.end);
      }

      const response = await fetch(`/api/audit/logs?${params}`);
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch('/api/audit/export/compliance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_hash: patientHash })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_export_${new Date().toISOString()}.csv`;
        a.click();
      }
    } catch (error) {
      alert('Export failed');
    }
  };

  const filteredLogs = filterTask === 'All' 
    ? logs 
    : logs.filter(log => log.task === filterTask);

  const taskColors = {
    'DR': 'bg-yellow-50 border-yellow-200',
    'Glaucoma': 'bg-red-50 border-red-200',
    'Refraction': 'bg-purple-50 border-purple-200'
  };

  const taskBadgeColors = {
    'DR': 'bg-yellow-100 text-yellow-800',
    'Glaucoma': 'bg-red-100 text-red-800',
    'Refraction': 'bg-purple-100 text-purple-800'
  };

  return (
    <div className="max-w-5xl mx-auto p-6 bg-white rounded-lg shadow space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2 mb-1">
            <FileText className="text-blue-600" />
            Audit Trail
          </h2>
          <p className="text-sm text-gray-600">Immutable prediction and feedback logs</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-gray-700">Total Entries</p>
          <p className="text-2xl font-bold text-blue-600">{filteredLogs.length}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex gap-2 flex-wrap">
          {(['All', 'DR', 'Glaucoma', 'Refraction'] as const).map(task => (
            <button
              key={task}
              onClick={() => setFilterTask(task)}
              className={`px-3 py-1 rounded text-sm font-medium transition ${
                filterTask === task
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {task}
            </button>
          ))}
        </div>
        <button
          onClick={handleExport}
          className="ml-auto flex items-center gap-2 px-4 py-1 bg-green-600 text-white rounded hover:bg-green-700 font-medium transition"
        >
          <Download size={16} />
          Export (Compliance)
        </button>
      </div>

      {/* Logs List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No audit logs found</div>
        ) : (
          filteredLogs.map(log => (
            <div
              key={log.log_id}
              className={`p-4 border-l-4 rounded cursor-pointer transition hover:shadow-md ${taskColors[log.task]}`}
              onClick={() => setExpandedId(expandedId === log.log_id ? null : log.log_id)}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${taskBadgeColors[log.task]}`}>
                      {log.task}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Calendar size={12} />
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="font-semibold text-gray-800">{log.prediction}</p>
                  <div className="flex gap-4 text-sm text-gray-600 mt-1">
                    <span>Confidence: <span className="font-bold">{(log.confidence * 100).toFixed(1)}%</span></span>
                    <span>Model: {log.model_version}</span>
                    {log.correction_applied && (
                      <span className="text-blue-600 font-semibold">
                        Correction: {log.correction_factor?.toFixed(2)}x
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right text-xs text-gray-500">
                  <p>ID: {log.log_id.substring(0, 8)}...</p>
                  <p>{log.consent_verified ? '✓ Consent' : '⚠ No Consent'}</p>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedId === log.log_id && (
                <div className="mt-4 pt-4 border-t space-y-3 text-sm">
                  {/* Core Prediction Info */}
                  <div className="bg-white bg-opacity-50 rounded p-3 space-y-2">
                    <h4 className="font-semibold text-gray-800">Prediction Details</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-gray-600">Log ID</p>
                        <p className="font-mono text-gray-800">{log.log_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Patient Hash</p>
                        <p className="font-mono text-gray-800">{log.anonymized_patient_hash.substring(0, 16)}...</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Consent Verified</p>
                        <p className="font-bold text-green-700">{log.consent_verified ? 'Yes' : 'No'}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Ethics Approval</p>
                        <p className="font-mono text-gray-800">{log.ethics_approval_id}</p>
                      </div>
                    </div>
                  </div>

                  {/* Clinician Feedback (if available) */}
                  {log.clinician_feedback && (
                    <div className="bg-blue-50 rounded p-3 space-y-2 border border-blue-200">
                      <h4 className="font-semibold text-blue-900">Clinician Feedback</h4>
                      <div>
                        <p className="text-xs text-blue-700">
                          <span className="font-semibold">Clinician ID:</span> {log.clinician_feedback.clinician_id}
                        </p>
                        <p className="text-xs text-blue-700">
                          <span className="font-semibold">Agreement:</span> {log.clinician_feedback.clinician_agreement}/5
                        </p>
                        <p className="text-xs text-blue-700">
                          <span className="font-semibold">Submitted:</span>{' '}
                          {new Date(log.clinician_feedback.feedback_timestamp).toLocaleString()}
                        </p>
                      </div>
                      {log.clinician_feedback.clinician_feedback && (
                        <p className="text-xs italic text-blue-800 bg-white bg-opacity-50 p-2 rounded">
                          "{log.clinician_feedback.clinician_feedback}"
                        </p>
                      )}
                    </div>
                  )}

                  {/* Immutability Note */}
                  <div className="text-xs text-gray-500 italic">
                    This record is immutable and cannot be modified after creation (append-only audit trail).
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Info Footer */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded text-sm text-blue-900">
        <p className="font-semibold mb-1">Audit Trail Design (P0.6)</p>
        <ul className="text-xs space-y-1 list-disc list-inside">
          <li>All predictions logged immutably with timestamp</li>
          <li>Clinician feedback added separately (doesn't modify original prediction)</li>
          <li>Patient identifiers anonymized (SHA-256 hash only)</li>
          <li>Export format removes all PII for regulatory compliance</li>
        </ul>
      </div>
    </div>
  );
};
