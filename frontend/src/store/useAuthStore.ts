import { create } from 'zustand'
import { authService, type User, type LoginRequest } from '../services/api'
import { clearAccessToken, setAccessToken } from '../utils/authSession'

interface AuthState {
    user: User | null
    token: string | null
    isAuthenticated: boolean
    isLoading: boolean
    hasCheckedAuth: boolean
    error: string | null

    // Actions
    login: (credentials: LoginRequest) => Promise<void>
    logout: () => Promise<void>
    checkAuth: () => Promise<void>
    clearSession: () => void
    clearError: () => void
    updateUser: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    hasCheckedAuth: false,
    error: null,

    /**
     * Login user with email and password
     */
    login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null })

        try {
            const response = await authService.login(credentials)

            setAccessToken(response.access_token)

            // Update state
            set({
                user: response.user,
                token: response.access_token,
                isAuthenticated: true,
                isLoading: false,
                hasCheckedAuth: true,
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
                hasCheckedAuth: true,
                error: errorMessage,
            })

            console.error('✗ Login failed:', errorMessage)
            throw error
        }
    },

    /**
     * Logout user and clear auth data
     */
    logout: async () => {
        try {
            await authService.logout()
        } finally {
            clearAccessToken()
            set({
                user: null,
                token: null,
                isAuthenticated: false,
                isLoading: false,
                hasCheckedAuth: true,
                error: null,
            })

            console.log('✓ Logged out successfully')
        }
    },

    /**
     * Check if user is authenticated by validating token
     */
    checkAuth: async () => {
        set({ isLoading: true })

        try {
            const user = await authService.getCurrentUser()

            set({
                user,
                isAuthenticated: true,
                isLoading: false,
                hasCheckedAuth: true,
                error: null,
            })
        } catch (error) {
            clearAccessToken()

            set({
                user: null,
                token: null,
                isAuthenticated: false,
                isLoading: false,
                hasCheckedAuth: true,
            })
        }
    },

    clearSession: () => {
        clearAccessToken()
        set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            hasCheckedAuth: true,
            error: null,
        })
    },

    /**
     * Clear error message
     */
    clearError: () => {
        set({ error: null })
    },

    /**
     * Update cached user profile data in store.
     * This keeps header/profile UI in sync even without a backend update endpoint.
     */
    updateUser: (updates: Partial<User>) => {
        set((state) => {
            if (!state.user) return state

            const updatedUser: User = {
                ...state.user,
                ...updates,
            }

            return {
                ...state,
                user: updatedUser,
            }
        })
    },
}))
