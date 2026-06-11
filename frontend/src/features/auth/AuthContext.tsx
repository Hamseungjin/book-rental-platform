import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { userApi } from '../../api/endpoints'
import { getStoredUserId, setStoredUserId } from '../../api/client'
import type { RoleName } from '../../types/api'

interface AuthValue { userId: string; setUserId: (id: string) => void; userName?: string; roles: RoleName[]; isLoading: boolean; userError: boolean; hasRole: (role: RoleName) => boolean }
const AuthContext = createContext<AuthValue | null>(null)
export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserIdState] = useState(getStoredUserId)
  const numericId = Number(userId)
  const query = useQuery({ queryKey: ['current-user', userId], queryFn: () => userApi.get(numericId), enabled: Number.isInteger(numericId) && numericId > 0, retry: false })
  const setUserId = useCallback((id: string) => { setStoredUserId(id); setUserIdState(id) }, [])
  const value = useMemo<AuthValue>(() => ({ userId, setUserId, userName: query.data?.name, roles: query.data?.roles ?? [], isLoading: query.isLoading, userError: query.isError, hasRole: role => query.data?.roles.includes(role) ?? false }), [userId, setUserId, query.data, query.isLoading, query.isError])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export const useAuth = () => { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider가 필요합니다.'); return value }
