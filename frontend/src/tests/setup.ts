import '@testing-library/jest-dom';
import { expect, afterEach, vi, beforeEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock API responses for testing
export const mockApiResponses = {
  mtlAnalysis: {
    dr_prediction: {
      class: 'Mild',
      confidence: 0.87,
      class_scores: {
        'No DR': 0.05,
        'Mild': 0.87,
        'Moderate': 0.06,
        'Severe': 0.01,
        'Proliferative': 0.01,
      },
    },
    glaucoma_prediction: {
      prediction: 'Normal',
      confidence: 0.92,
      original_logit: 0.523,
      corrected_logit: 0.525,
      correction_factor: 1.003,
    },
    refraction_prediction: {
      sphere: -0.50,
      cylinder: -0.25,
      axis: 180,
      confidence: 0.88,
    },
    correction_factor: 1.003,
    audit_log_id: 'LOG_TEST_001',
    timestamp: new Date().toISOString(),
  },

  ccrMetrics: {
    global_ccr: 0.87,
    h3_hypothesis_status: 'PASS',
    total_cases: 35,
    cases_above_threshold: 30,
    task_specific_ccr: {
      dr_ccr: 0.89,
      glaucoma_ccr: 0.85,
      refraction_ccr: 0.87,
    },
    expert_metrics: [
      {
        expert_id: 'DR_001',
        dr_agreement: 0.9,
        glaucoma_agreement: 0.85,
        refraction_agreement: 0.88,
        avg_agreement: 0.88,
      },
    ],
    confidence_interval: {
      lower: 0.82,
      upper: 0.92,
    },
  },

  auditLogs: {
    logs: [
      {
        log_id: 'LOG_TEST_001',
        timestamp: new Date().toISOString(),
        anonymized_patient_hash: 'a1b2c3d4e5f6...',
        task: 'DR',
        prediction: 'Mild',
        confidence: 0.87,
        correction_applied: false,
        clinician_feedback: {
          clinician_id: 'DR_001',
          clinician_agreement: 4,
          feedback: 'Good prediction',
        },
      },
    ],
    count: 1,
  },

  expertReview: {
    success: true,
    review_id: 'REV_001',
    patient_id: 'LOCAL_PATIENT_001',
    dr_assessment: 4,
    glaucoma_assessment: 4,
    refraction_assessment: 5,
    clinician_id: 'DR_001',
    timestamp: new Date().toISOString(),
  },

  patientRegistration: {
    patient_id: 'LOCAL_PATIENT_001',
    anonymized_patient_id: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
    age_bracket: '45-50',
    diabetes_status: 'Type 2',
    iop_left: 15.2,
    iop_right: 16.1,
    registration_date: new Date().toISOString(),
  },

  consentRecord: {
    consent_id: 'CONS_001',
    patient_id: 'LOCAL_PATIENT_001',
    consent_type: 'image_analysis',
    is_valid: true,
    expiry_date: '2027-12-31',
    recording_date: new Date().toISOString(),
  },
};

// Mock fetch globally
global.fetch = vi.fn();

// Helper to reset all mocks
export const resetAllMocks = () => {
  vi.clearAllMocks();
  (global.fetch as any).mockClear();
};

// Helper to mock fetch success
export const mockFetchSuccess = (data: any) => {
  (global.fetch as any).mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: async () => data,
  });
};

// Helper to mock fetch error
export const mockFetchError = (status: number = 500, message: string = 'Server error') => {
  (global.fetch as any).mockResolvedValueOnce({
    ok: false,
    status,
    json: async () => ({ detail: message }),
  });
};

// Setup global test environment
beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});
