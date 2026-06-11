import type { ReactNode } from 'react'
import type { RoleName } from '../types/api'
import { useAuth } from '../features/auth/AuthContext'
import { EmptyState } from './ui/Feedback'
export function RequireRole({ role, children }: { role: RoleName; children: ReactNode }) { const { hasRole, userId } = useAuth(); if (!userId) return <EmptyState title="사용자 ID를 입력해 주세요." description="상단 사용자 선택 영역에서 API 요청에 사용할 ID를 설정할 수 있습니다."/>; if (!hasRole(role)) return <EmptyState title={`${role} 역할이 필요합니다.`} description="프론트 역할 확인은 메뉴 UX용이며, 최종 권한은 백엔드가 검증합니다."/>; return children }
