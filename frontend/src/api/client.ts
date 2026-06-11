import axios, { AxiosError } from 'axios'
import type { ApiErrorResponse } from '../types/api'

const USER_ID_KEY = 'book-rental.current-user-id'
export const getStoredUserId = () => localStorage.getItem(USER_ID_KEY) ?? ''
export const setStoredUserId = (id: string) => id ? localStorage.setItem(USER_ID_KEY, id) : localStorage.removeItem(USER_ID_KEY)

export const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080', timeout: 10000 })
apiClient.interceptors.request.use((config) => {
  const userId = getStoredUserId()
  if (userId) {
    config.headers['X-User-Id'] = userId
    if (config.url?.startsWith('/api/admin')) config.headers['X-Admin-Id'] = userId
  }
  return config
})

export function getApiError(error: unknown): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    const data = error.response?.data
    const fields = data?.fieldErrors ? Object.values(data.fieldErrors).join(' · ') : ''
    return [data?.message, fields].filter(Boolean).join(' — ') || (error as AxiosError).message
  }
  return error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
}
