import axios from 'axios'

// Base URL configuration - Auth Service for now (will be API Gateway later)
const API_BASE_URL = 'http://localhost:8001'
const PATIENT_API_BASE_URL = 'http://localhost:8002'
const IMAGING_API_BASE_URL = 'http://localhost:8003'
const ML_API_BASE_URL = 'http://localhost:8004'

// Create Axios instance for Auth Service
const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create Axios instance for Patient Service
const patientApi = axios.create({
  baseURL: PATIENT_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create Axios instance for Imaging Service
const imagingApi = axios.create({
  baseURL: IMAGING_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create Axios instance for ML Service
const mlApi = axios.create({
  baseURL: ML_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Attach JWT token to all requests
const attachTokenInterceptor = (config: any) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}

// Response Interceptor: Handle 401 Unauthorized
const handleUnauthorizedInterceptor = (error: any) => {
  if (error.response?.status === 401) {
    // Token expired or invalid - clear auth and redirect to login
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    window.location.href = '/login'
  }
  return Promise.reject(error)
}

// Apply interceptors to all instances
authApi.interceptors.request.use(attachTokenInterceptor)
authApi.interceptors.response.use((response) => response, handleUnauthorizedInterceptor)

patientApi.interceptors.request.use(attachTokenInterceptor)
patientApi.interceptors.response.use((response) => response, handleUnauthorizedInterceptor)

imagingApi.interceptors.request.use(attachTokenInterceptor)
imagingApi.interceptors.response.use((response) => response, handleUnauthorizedInterceptor)

mlApi.interceptors.request.use(attachTokenInterceptor)
mlApi.interceptors.response.use((response) => response, handleUnauthorizedInterceptor)



// ============ Type Definitions ============

export interface User {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'doctor'
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: User
  access_token: string
  token_type: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  role?: 'admin' | 'doctor'
}

export interface Patient {
  id: string
  full_name: string
  dob: string
  gender: string
  diabetes_status: boolean
  created_at: string
  updated_at: string
}

export interface PatientCreateRequest {
  full_name: string
  dob: string
  gender: string
  diabetes_status?: boolean
}

export interface ImageRecord {
  id: number
  patient_id: string
  image_type: 'FUNDUS' | 'OCT'
  file_path: string
  file_name: string
  file_size: number
  content_type: string
  uploaded_at: string
  url?: string // Presigned URL for accessing the image
}

export interface ImageListResponse {
  total: number
  images: ImageRecord[]
}

export interface AnalysisResult {

  refraction: {
    sphere: number
    cylinder: number
    axis: number
  }
  pathology: {
    diabetic_retinopathy: {
      status: 'Healthy' | 'Warning' | 'Severe'
      score: number
    }
    glaucoma: {
      status: 'Healthy' | 'Warning' | 'Severe'
      score: number
    }
  }
  reasoning: string[]
}

// ============ Auth Service API ============

export const authService = {
  /**
   * Login user and receive JWT token
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await authApi.post<LoginResponse>('/login', credentials)
    return response.data
  },

  /**
   * Register new user
   */
  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await authApi.post<User>('/register', userData)
    return response.data
  },

  /**
   * Get current authenticated user
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await authApi.get<User>('/me')
    return response.data
  },

  /**
   * Get all users (admin only)
   */
  getAllUsers: async (): Promise<User[]> => {
    const response = await authApi.get<User[]>('/admin/users')
    return response.data
  },
}

// ============ Patient Service API ============

export const patientService = {
  /**
   * Get all patients with optional search
   */
  getPatients: async (search?: string, skip = 0, limit = 100): Promise<Patient[]> => {
    const params = new URLSearchParams()
    if (search) params.append('search', search)
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())

    const response = await patientApi.get<Patient[]>(`/patients?${params.toString()}`)
    return response.data
  },

  /**
   * Get single patient by ID
   */
  getPatient: async (patientId: string): Promise<Patient> => {
    const response = await patientApi.get<Patient>(`/patients/${patientId}`)
    return response.data
  },

  /**
   * Create new patient
   */
  createPatient: async (patientData: PatientCreateRequest): Promise<Patient> => {
    const response = await patientApi.post<Patient>('/patients', patientData)
    return response.data
  },

  /**
   * Update patient
   */
  updatePatient: async (patientId: string, patientData: Partial<PatientCreateRequest>): Promise<Patient> => {
    const response = await patientApi.put<Patient>(`/patients/${patientId}`, patientData)
    return response.data
  },

  /**
   * Delete patient
   */
  deletePatient: async (patientId: string): Promise<void> => {
    await patientApi.delete(`/patients/${patientId}`)
  },

  /**
   * Get patient statistics
   */
  getStatistics: async (): Promise<{
    total_patients: number
    diabetes_patients: number
    non_diabetes_patients: number
    diabetes_percentage: number
  }> => {
    const response = await patientApi.get('/patients/stats/summary')
    return response.data
  },
}

// ============ Imaging Service API ============

export const imagingService = {
  /**
   * Upload image for a patient
   */
  uploadPatientImage: async (patientId: string, formData: FormData): Promise<ImageRecord> => {
    const response = await imagingApi.post<ImageRecord>(`/upload/${patientId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Get all images for a patient
   */
  getPatientImages: async (patientId: string, imageType?: 'FUNDUS' | 'OCT'): Promise<ImageListResponse> => {
    const params = imageType ? { image_type: imageType } : {}
    const response = await imagingApi.get<ImageListResponse>(`/images/${patientId}`, { params })
    return response.data
  },

  /**
   * Get a specific image by ID
   */
  getImageById: async (imageId: number): Promise<ImageRecord> => {
    const response = await imagingApi.get<ImageRecord>(`/image/${imageId}`)
    return response.data
  },

  /**
   * Delete an image
   */
  deleteImage: async (imageId: number): Promise<void> => {
    await imagingApi.delete(`/image/${imageId}`)
  },

  /**
   * Get upload statistics
   */
  getStatistics: async (): Promise<{
    total_images: number
    total_size_bytes: number
    total_size_mb: number
    by_type: { FUNDUS: number; OCT: number }
  }> => {
    const response = await imagingApi.get('/stats')
    return response.data
  },

  /**
   * Get recent images (for polling/notifications)
   */
  getRecentImages: async (limit: number = 10): Promise<ImageRecord[]> => {
    const response = await imagingApi.get('/images/recent', {
      params: { limit }
    })
    return response.data
  },
}

// Convenience function for backward compatibility
export const uploadPatientImage = imagingService.uploadPatientImage

// ============ ML Service API ============

export const mlService = {
  /**
   * Predict refraction measurements
   */
  predictRefraction: async (file: File): Promise<{
    sphere: number
    cylinder: number
    axis: number
  }> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await mlApi.post('/predict/refraction', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Predict pathology (DR grade and glaucoma risk)
   */
  predictPathology: async (file: File): Promise<{
    dr_grade: number
    glaucoma_risk: number
  }> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await mlApi.post('/predict/pathology', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Explain pathology prediction with Grad-CAM heatmap
   */
  explainPathology: async (file: File): Promise<{
    diagnosis: {
      dr_grade: number
      glaucoma_risk: number
      dr_class: string
      confidence: number
    }
    heatmap_base64: string
    processing_time_ms: number
    explanation: string
  }> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await mlApi.post('/explain/pathology', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

// ============ Analysis Service (Imaging + ML) ============

/**
 * Analyze a medical scan - uploads to imaging service then gets ML predictions
 * 
 * @param file - The scan image file
 * @param patientId - Optional patient ID to associate the image with
 * @returns Analysis results with refraction and pathology predictions
 */
export const analyzeScan = async (
  file: File,
  patientId?: string
): Promise<AnalysisResult> => {
  console.log(`Analyzing scan: ${file.name}`)

  try {
    // Step 1: Upload image to imaging service (if patient ID provided)
    if (patientId) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        await imagingService.uploadPatientImage(patientId, formData)
        console.log('✓ Image saved to imaging service')
      } catch (error) {
        console.warn('⚠️ Failed to save image to imaging service:', error)
        // Continue with ML prediction even if upload fails
      }
    }

    // Step 2: Get ML predictions
    const [refractionResult, pathologyResult] = await Promise.all([
      mlService.predictRefraction(file),
      mlService.predictPathology(file)
    ])

    console.log('✓ ML predictions received')

    // Map ML results to AnalysisResult format
    const result: AnalysisResult = {
      refraction: {
        sphere: refractionResult.sphere,
        cylinder: refractionResult.cylinder,
        axis: refractionResult.axis
      },
      pathology: {
        diabetic_retinopathy: {
          status: pathologyResult.dr_grade >= 3 ? 'Severe' :
            pathologyResult.dr_grade >= 1 ? 'Warning' : 'Healthy',
          score: pathologyResult.dr_grade * 25 // Convert 0-4 to 0-100
        },
        glaucoma: {
          status: pathologyResult.glaucoma_risk >= 0.7 ? 'Severe' :
            pathologyResult.glaucoma_risk >= 0.4 ? 'Warning' : 'Healthy',
          score: Math.round(pathologyResult.glaucoma_risk * 100)
        }
      },
      reasoning: [
        generateDRReasoning(pathologyResult.dr_grade),
        generateGlaucomaReasoning(pathologyResult.glaucoma_risk),
        generateRefractionReasoning(refractionResult)
      ]
    }

    return result

  } catch (error: any) {
    console.error('✗ Analysis failed:', error)
    throw new Error(error.response?.data?.detail || 'Analysis failed. Please try again.')
  }
}

// Helper functions to generate reasoning text
function generateDRReasoning(grade: number): string {
  const descriptions = [
    'No signs of diabetic retinopathy detected. Retinal blood vessels appear healthy.',
    'Mild non-proliferative diabetic retinopathy detected. Minor microaneurysms observed.',
    'Moderate non-proliferative diabetic retinopathy detected. Multiple microaneurysms and hemorrhages present.',
    'Severe non-proliferative diabetic retinopathy detected. Extensive retinal changes observed.',
    'Proliferative diabetic retinopathy detected. Abnormal new blood vessel growth observed - requires immediate attention.'
  ]
  return descriptions[grade] || descriptions[0]
}

function generateGlaucomaReasoning(risk: number): string {
  if (risk >= 0.7) {
    return `High intraocular pressure indicators detected (risk: ${(risk * 100).toFixed(0)}%). Optic disc cupping suggests glaucomatous changes.`
  } else if (risk >= 0.4) {
    return `Moderate glaucoma risk detected (${(risk * 100).toFixed(0)}%). Some optic nerve changes observed.`
  } else {
    return `Low glaucoma risk (${(risk * 100).toFixed(0)}%). Optic disc appears healthy.`
  }
}

function generateRefractionReasoning(refraction: { sphere: number; cylinder: number; axis: number }): string {
  const { sphere, cylinder, axis } = refraction
  let description = ''

  if (Math.abs(sphere) < 0.5) {
    description = 'Minimal refractive error detected.'
  } else if (sphere < -6) {
    description = 'High myopia (nearsightedness) detected.'
  } else if (sphere < 0) {
    description = 'Myopia (nearsightedness) detected.'
  } else if (sphere > 3) {
    description = 'Significant hyperopia (farsightedness) detected.'
  } else if (sphere > 0) {
    description = 'Mild hyperopia (farsightedness) detected.'
  }

  if (Math.abs(cylinder) > 0.5) {
    description += ` Astigmatism correction needed (${Math.abs(cylinder).toFixed(2)}D at ${axis}°).`
  }

  return description + ` Prescription: SPH ${sphere.toFixed(2)} CYL ${cylinder.toFixed(2)} × ${axis.toFixed(0)}°`
}

// Legacy mock function (deprecated - use analyzeScan instead)
export const uploadScan = analyzeScan


// Export default auth API instance for backward compatibility
export default authApi

