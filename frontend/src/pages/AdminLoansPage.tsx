import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { adminApi, loansApi } from '../api/endpoints'
import { getApiError } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { RequireRole } from '../components/RequireRole'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { EmptyState, ErrorAlert, LoadingState } from '../components/ui/Feedback'
import { formatDate } from '../utils/format'
import { useAuth } from '../features/auth/AuthContext'
export function AdminLoansPage(){const qc=useQueryClient();const {userId,hasRole}=useAuth();const q=useQuery({queryKey:['admin-loans',userId],queryFn:adminApi.loans,enabled:hasRole('ADMIN')});const m=useMutation({mutationFn:loansApi.returnBook,onSuccess:()=>{qc.invalidateQueries({queryKey:['admin-loans']});qc.invalidateQueries({queryKey:['admin-overdue-loans']});qc.invalidateQueries({queryKey:['admin-dashboard']})}});return <RequireRole role="ADMIN"><PageHeader title="현재 대출 관리" description="대출 중이거나 연체된 건을 확인하고 반납 처리합니다." action={<Link className="text-sm font-semibold text-rose-700" to="/admin/loans/overdue">연체 목록 보기 →</Link>}/>{m.isError&&<div className="mb-4"><ErrorAlert message={getApiError(m.error)}/></div>}{q.isLoading?<LoadingState/>:q.isError?<ErrorAlert message={getApiError(q.error)}/>:!q.data?.length?<EmptyState title="현재 대출 중인 책이 없습니다."/>:<LoanTable loans={q.data} onReturn={id=>m.mutate(id)} pending={m.isPending}/>}</RequireRole>}
export function LoanTable({loans,onReturn,pending}:{loans:import('../types/api').Loan[];onReturn:(id:number)=>void;pending:boolean}){return <div className="table-wrap"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-xs text-slate-500"><tr><th className="p-4">책</th><th className="p-4">대여자/등록자</th><th className="p-4">기간</th><th className="p-4">상태</th><th className="p-4">처리</th></tr></thead><tbody className="divide-y">{loans.map(l=><tr key={l.id}><td className="p-4"><strong>{l.bookTitle}</strong><div className="text-xs text-slate-500">{l.quantity}권 · 대출 #{l.id}</div></td><td className="p-4">{l.borrowerName}<div className="text-xs text-slate-500">등록자 {l.lenderName}</div></td><td className="p-4">{formatDate(l.loanedAt)}<div className="text-xs text-slate-500">기한 {formatDate(l.dueAt)}</div></td><td className="p-4"><Badge value={l.status}/></td><td className="p-4"><Button variant="secondary" disabled={pending} onClick={()=>onReturn(l.id)}>반납 처리</Button></td></tr>)}</tbody></table></div>}
