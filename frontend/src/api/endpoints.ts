import { apiClient } from './client'
import type { Book, BookUpsertInput, BorrowRequest, Dashboard, Loan, UserResponse } from '../types/api'

export const userApi = { get: (id: number) => apiClient.get<UserResponse>(`/api/users/${id}`).then(r => r.data) }
export const booksApi = {
  list: () => apiClient.get<Book[]>('/api/books').then(r => r.data),
  get: (id: number) => apiClient.get<Book>(`/api/books/${id}`).then(r => r.data),
  request: (bookListingId: number, quantity: number) => apiClient.post<BorrowRequest>('/api/borrow-requests', { bookListingId, quantity }).then(r => r.data),
}
export const borrowerApi = { requests: () => apiClient.get<BorrowRequest[]>('/api/borrow-requests/me').then(r => r.data) }
export const lenderApi = {
  books: () => apiClient.get<Book[]>('/api/lender/books').then(r => r.data),
  create: (data: BookUpsertInput) => apiClient.post<Book>('/api/lender/books', data).then(r => r.data),
  update: (id: number, data: BookUpsertInput) => apiClient.patch<Book>(`/api/lender/books/${id}`, data).then(r => r.data),
}
export const adminApi = {
  dashboard: () => apiClient.get<Dashboard>('/api/admin/dashboard').then(r => r.data),
  pendingBooks: () => apiClient.get<Book[]>('/api/admin/books/pending').then(r => r.data),
  approveBook: (id: number) => apiClient.patch<Book>(`/api/admin/books/${id}/approve`).then(r => r.data),
  rejectBook: (id: number, memo: string) => apiClient.patch<Book>(`/api/admin/books/${id}/reject`, { memo }).then(r => r.data),
  requests: () => apiClient.get<BorrowRequest[]>('/api/admin/borrow-requests').then(r => r.data),
  approveRequest: (id: number) => apiClient.patch<Loan>(`/api/admin/borrow-requests/${id}/approve`).then(r => r.data),
  rejectRequest: (id: number, memo: string) => apiClient.patch<BorrowRequest>(`/api/admin/borrow-requests/${id}/reject`, { memo }).then(r => r.data),
  loans: () => apiClient.get<Loan[]>('/api/admin/loans').then(r => r.data),
  overdueLoans: () => apiClient.get<Loan[]>('/api/admin/loans/overdue').then(r => r.data),
}
export const loansApi = { returnBook: (id: number) => apiClient.patch<Loan>(`/api/loans/${id}/return`).then(r => r.data) }
