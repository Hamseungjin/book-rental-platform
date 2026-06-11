export type RoleName = 'BORROWER' | 'LENDER' | 'ADMIN'
export type BookFormat = 'PHYSICAL_BOOK' | 'PDF'
export type BookListingStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'INACTIVE' | 'DELETED'
export type BorrowRequestStatus = 'REQUESTED' | 'APPROVED' | 'REJECTED' | 'CANCELED' | 'EXPIRED'
export type LoanStatus = 'LOANED' | 'RETURNED' | 'OVERDUE' | 'LOST' | 'CANCELED'

export interface UserResponse { id: number; name: string; email: string; active: boolean; roles: RoleName[]; createdAt: string; updatedAt: string }
export interface BookFile { id: number; originalFilename: string; storedFileUrl: string; mimeType: string; fileSize: number }
export interface Book { id: number; lenderId: number; lenderName: string; title: string; author: string; category: string; description: string; format: BookFormat; totalQuantity: number; availableQuantity: number; defaultLoanDays: number; status: BookListingStatus; rejectionMemo: string | null; file: BookFile | null; createdAt: string; updatedAt: string }
export interface BookFileInput { originalFilename: string; storedFileUrl: string; mimeType: string; fileSize: number }
export interface BookUpsertInput { title: string; author: string; category: string; description: string; format: BookFormat; totalQuantity: number; availableQuantity: number; defaultLoanDays: number; file: BookFileInput | null }
export interface BorrowRequest { id: number; borrowerId: number; borrowerName: string; bookListingId: number; bookTitle: string; quantity: number; status: BorrowRequestStatus; requestedAt: string; approvedAt: string | null; rejectedAt: string | null; canceledAt: string | null }
export interface Loan { id: number; borrowRequestId: number; borrowerId: number; borrowerName: string; lenderId: number; lenderName: string; bookListingId: number; bookTitle: string; quantity: number; loanedAt: string; dueAt: string; returnedAt: string | null; status: LoanStatus }
export interface Dashboard { totalUsers: number; borrowerUsers: number; lenderUsers: number; totalBooks: number; pendingBooks: number; approvedBooks: number; totalBorrowRequests: number; activeLoans: number; returnedLoans: number; overdueLoans: number; recentBooks: Book[]; recentBorrowRequests: BorrowRequest[] }
export interface ApiErrorResponse { timestamp?: string; status?: number; code?: string; message?: string; fieldErrors?: Record<string, string> }
