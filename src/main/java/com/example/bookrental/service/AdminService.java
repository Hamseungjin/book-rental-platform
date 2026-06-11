package com.example.bookrental.service;

import com.example.bookrental.domain.*;
import com.example.bookrental.domain.enums.*;
import com.example.bookrental.dto.*;
import com.example.bookrental.exception.NotFoundException;
import com.example.bookrental.repository.*;
import com.example.bookrental.security.AuthorizationService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminService {
    private final BookListingRepository books; private final BorrowRequestRepository requests; private final LoanHistoryRepository loans;
    private final UserRepository users; private final AdminActivityLogRepository logs; private final AuthorizationService authorization;
    private final DtoMapper mapper; private final Clock clock;
    public AdminService(BookListingRepository books, BorrowRequestRepository requests, LoanHistoryRepository loans,
                        UserRepository users, AdminActivityLogRepository logs, AuthorizationService authorization, DtoMapper mapper, Clock clock) {
        this.books = books; this.requests = requests; this.loans = loans; this.users = users; this.logs = logs;
        this.authorization = authorization; this.mapper = mapper; this.clock = clock;
    }
    @Transactional(readOnly = true)
    public List<BookDtos.Response> pendingBooks(Long adminId) {
        requireAdmin(adminId); return books.findAllByStatusOrderByCreatedAtDesc(BookStatus.PENDING).stream().map(mapper::book).toList();
    }
    @Transactional
    public BookDtos.Response approveBook(Long adminId, Long bookId) {
        User admin = requireAdmin(adminId);
        BookListing book = books.findByIdForUpdate(bookId).orElseThrow(() -> new NotFoundException("책", bookId));
        book.approve(); log(admin, AdminAction.BOOK_APPROVED, AdminTargetType.BOOK_LISTING, bookId, null);
        return mapper.book(book);
    }
    @Transactional
    public BookDtos.Response rejectBook(Long adminId, Long bookId, String memo) {
        User admin = requireAdmin(adminId);
        BookListing book = books.findByIdForUpdate(bookId).orElseThrow(() -> new NotFoundException("책", bookId));
        book.reject(memo); log(admin, AdminAction.BOOK_REJECTED, AdminTargetType.BOOK_LISTING, bookId, memo);
        return mapper.book(book);
    }
    @Transactional(readOnly = true)
    public List<BorrowRequestDtos.Response> allRequests(Long adminId) {
        requireAdmin(adminId); return requests.findAllByOrderByRequestedAtDesc().stream().map(mapper::borrowRequest).toList();
    }
    @Transactional
    public LoanDtos.Response approveBorrowRequest(Long adminId, Long requestId) {
        User admin = requireAdmin(adminId);
        BorrowRequest request = requests.findByIdForUpdate(requestId).orElseThrow(() -> new NotFoundException("대여 요청", requestId));
        BookListing book = books.findByIdForUpdate(request.getBookListing().getId()).orElseThrow(() -> new NotFoundException("책", request.getBookListing().getId()));
        book.ensureApproved();
        book.decreaseAvailableQuantity(request.getQuantity());
        LocalDateTime now = LocalDateTime.now(clock);
        request.approve(now);
        LoanHistory loan = loans.save(new LoanHistory(request, now, now.plusDays(book.getDefaultLoanDays())));
        log(admin, AdminAction.BORROW_REQUEST_APPROVED, AdminTargetType.BORROW_REQUEST, requestId, null);
        return mapper.loan(loan);
    }
    @Transactional
    public BorrowRequestDtos.Response rejectBorrowRequest(Long adminId, Long requestId, String memo) {
        User admin = requireAdmin(adminId);
        BorrowRequest request = requests.findByIdForUpdate(requestId).orElseThrow(() -> new NotFoundException("대여 요청", requestId));
        request.reject(LocalDateTime.now(clock));
        log(admin, AdminAction.BORROW_REQUEST_REJECTED, AdminTargetType.BORROW_REQUEST, requestId, memo);
        return mapper.borrowRequest(request);
    }
    @Transactional(readOnly = true)
    public List<LoanDtos.Response> loans(Long adminId) {
        requireAdmin(adminId); return loans.findAllByStatusInOrderByDueAtAsc(List.of(LoanStatus.LOANED, LoanStatus.OVERDUE)).stream().map(mapper::loan).toList();
    }
    @Transactional
    public List<LoanDtos.Response> overdueLoans(Long adminId) {
        requireAdmin(adminId);
        List<LoanHistory> overdue = loans.findOverdue(LocalDateTime.now(clock));
        overdue.forEach(LoanHistory::markOverdue);
        return overdue.stream().map(mapper::loan).toList();
    }
    private User requireAdmin(Long adminId) {
        authorization.requireRole(adminId, RoleName.ADMIN);
        return users.findById(adminId).orElseThrow(() -> new NotFoundException("사용자", adminId));
    }
    private void log(User admin, AdminAction action, AdminTargetType type, Long targetId, String memo) {
        logs.save(new AdminActivityLog(admin, action, type, targetId, memo));
    }
}
