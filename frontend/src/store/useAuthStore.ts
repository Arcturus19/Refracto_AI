import { create } from 'zustand'
import { authService, type User, type LoginRequest } from '../services/api'

interface AuthState {
    user: User | null
    token: string | null
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null

    // Actions
    login: (credentials: LoginRequest) => Promise<void>
    logout: () => void
    checkAuth: () => Promise<void>
    clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    token: localStorage.getItem('auth_token'),
    isAuthenticated: false,
    isLoading: false,
    error: null,

    /**
     * Login user with email and password
     */
    login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null })

        try {
            const response = await authService.login(credentials)

            // Save token and user data to localStorage
            localStorage.setItem('auth_token', response.access_token)
            localStorage.setItem('user_data', JSON.stringify(response.user))

            // Update state
            set({
                user: response.user,
                token: response.access_token,
                isAuthenticated: true,
                isLoading: false,
                error: null,
            })

            console.log('✓ Login successful:', response.user.email)
        } catch (error: any) {
            const errorMessage = error.response?.data?.detail || 'Login failed. Please check your credentials.'

            set({
                user: null,
                token: null,
                isAuthenticated: false,
                isLoading: false,
                error: errorMessage,
            })

            console.error('✗ Login failed:', errorMessage)
            throw error
        }
    },

    /**
     * Logout user and clear auth data
     */
    logout: () => {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')

        set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: null,
        })

        console.log('✓ Logged out successfully')
    },

    /**
     * Check if user is authenticated by validating token
     */
    checkAuth: async () => {
        const token = localStorage.getItem('auth_token')

        if (!token) {
            set({ isAuthenticated: false, user: null })
            return
        }

        try {
            // Validate token by fetching current user
            const user = await authService.getCurrentUser()

            set({
                user,
                token,
                isAuthenticated: true,
                error: null,
            })
        } catch (error) {
            // Token is invalid or expired
            localStorage.removeItem('auth_token')
            localStorage.removeItem('user_data')

            set({
                user: null,
                token: null,
                isAuthenticated: false,
            })
        }
    },

    /**
     * Clear error message
     */
    clearError: () => {
        set({ error: null })
    },
}))
