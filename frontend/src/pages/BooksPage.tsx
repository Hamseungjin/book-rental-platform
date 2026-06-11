import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { booksApi } from '../api/endpoints'
import { PageHeader } from '../components/PageHeader'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { EmptyState, ErrorAlert, LoadingState } from '../components/ui/Feedback'
import { getApiError } from '../api/client'
export function BooksPage() { const q = useQuery({ queryKey:['books'], queryFn:booksApi.list }); return <><PageHeader title="승인된 도서" description="현재 대여 요청이 가능한 도서를 확인하세요."/>{q.isLoading ? <LoadingState/> : q.isError ? <ErrorAlert message={getApiError(q.error)}/> : !q.data?.length ? <EmptyState title="등록된 승인 도서가 없습니다."/> : <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{q.data.map(book => <Link key={book.id} to={`/books/${book.id}`}><Card className="h-full transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md"><div className="flex items-start justify-between gap-2"><Badge value={book.format}/><Badge value={book.status}/></div><h2 className="mt-5 text-lg font-bold">{book.title}</h2><p className="mt-1 text-sm text-slate-500">{book.author} · {book.category}</p><p className="mt-4 line-clamp-2 text-sm leading-6 text-slate-600">{book.description}</p><div className="mt-5 flex items-center justify-between border-t pt-4 text-sm"><span>기본 {book.defaultLoanDays}일</span><strong className={book.availableQuantity ? 'text-emerald-700' : 'text-rose-600'}>대여 가능 {book.availableQuantity}권</strong></div></Card></Link>)}</div>}</> }
