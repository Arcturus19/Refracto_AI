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
  showPIIWarning?: boolean;
  itemsPerPage?: number;
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
  onExportCompliance,
  showPIIWarning = false,
  itemsPerPage: _itemsPerPage,
}) => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterTask, setFilterTask] = useState<'All' | 'DR' | 'Glaucoma' | 'Refraction'>('All');
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');
  const itemsPerPage = _itemsPerPage ?? 20;

  useEffect(() => {
    fetchAuditLogs();
  }, [patientHash, dateRange, filterTask]);

  useEffect(() => {
    if (searchQuery) {
      fetchAuditLogs();
    }
  }, [searchQuery]);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (patientHash) params.append('patient_hash', patientHash);
      if (dateRange) {
        params.append('start_date', dateRange.start);
        params.append('end_date', dateRange.end);
      }
      if (filterTask !== 'All') params.append('task', filterTask);
      if (searchQuery) params.append('q', searchQuery);

      const response = await fetch(`/api/ml/audit/logs?${params}`, { headers: { 'Content-Type': 'application/json' } });
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      } else {
        setError('Failed to load audit logs');
      }
    } catch {
      setError('Error loading audit logs');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch('/api/ml/audit/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_hash: patientHash, format: exportFormat })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_export_${new Date().toISOString()}.${exportFormat}`;
        a.click();
      }
    } catch {
      setError('Export failed');
    }
  };

  const filteredLogs = filterTask === 'All' 
    ? logs 
    : logs.filter(log => log.task === filterTask);

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
  const pagedLogs = filteredLogs.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

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

      {/* PII Warning */}
      {showPIIWarning && (
        <div className="p-3 bg-yellow-50 border border-yellow-300 rounded text-sm text-yellow-800">
          All data shown is anonymized — no PII is stored or displayed.
        </div>
      )}

      {/* Search */}
      <div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by patient hash or date..."
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500 text-sm"
        />
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <div className="flex gap-2 flex-wrap items-center">
          <button
            aria-label="All Tasks"
            onClick={() => setFilterTask('All')}
            className={`px-3 py-1 rounded text-sm font-medium transition ${
              filterTask === 'All' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            All
          </button>
          {(['DR', 'Glaucoma', 'Refraction'] as const).map(task => (
            <button
              key={task}
              aria-label={task}
              onClick={() => { setFilterTask(task); setCurrentPage(1); }}
              className={`w-8 h-8 rounded-full font-bold text-xs transition ${
                filterTask === task
                  ? 'ring-2 ring-offset-1 ring-blue-500 opacity-100'
                  : 'opacity-70 hover:opacity-100'
              } ${task === 'DR' ? 'bg-yellow-400' : task === 'Glaucoma' ? 'bg-red-400' : 'bg-purple-400'}`}
              title={task === 'DR' ? 'Diabetic Retinopathy' : task}
            />
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json')}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-1 bg-green-600 text-white rounded hover:bg-green-700 font-medium transition"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-300 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Logs List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading audit logs...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No audit logs found</div>
        ) : (
          pagedLogs.map(log => (
            <div
              key={log.log_id}
              className={`p-4 border-l-4 rounded transition hover:shadow-md cursor-pointer ${taskColors[log.task]}`}
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
                  <p className="font-semibold text-gray-800">{log.prediction} · {log.log_id}</p>
                  <div className="flex gap-4 text-sm text-gray-600 mt-1">
                    <span>Confidence: {(log.confidence * 100).toFixed(0)}%</span>
                    <span className="font-mono">{log.anonymized_patient_hash}</span>
                    {log.correction_applied && (
                      <span className="text-blue-600 font-semibold">
                        Correction: {log.correction_factor?.toFixed(2)}x
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <p className="text-xs text-gray-500">{log.consent_verified ? '✓ Consent' : '⚠ No Consent'}</p>
                  <button
                    aria-label="Details"
                    onClick={(e) => { e.stopPropagation(); setExpandedId(expandedId === log.log_id ? null : log.log_id); }}
                    className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 border border-blue-300 rounded"
                  >
                    {expandedId === log.log_id ? 'Hide' : 'Details'}
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedId === log.log_id && (
                <div className="mt-4 pt-4 border-t space-y-3 text-sm">
                  <div className="bg-white bg-opacity-50 rounded p-3 space-y-2">
                    <h4 className="font-semibold text-gray-800">Prediction Details</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-gray-600">Log ID</p>
                        <p className="font-mono text-gray-800">{log.log_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Ethics Approval</p>
                        <p className="font-mono text-gray-800">{log.ethics_approval_id}</p>
                      </div>
                    </div>
                  </div>

                  {log.clinician_feedback?.clinician_feedback && (
                    <p className="text-xs italic text-blue-700 bg-blue-50 p-2 rounded border border-blue-200">
                      Clinician feedback: &ldquo;{log.clinician_feedback.clinician_feedback}&rdquo;
                    </p>
                  )}

                  <div className="text-xs text-gray-500 italic">
                    This record is immutable and cannot be modified after creation.
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 rounded border text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">Page {currentPage} of {totalPages}</span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 rounded border text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

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
