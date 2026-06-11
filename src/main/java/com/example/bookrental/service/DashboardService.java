package com.example.bookrental.service;

import com.example.bookrental.domain.enums.*;
import com.example.bookrental.dto.DashboardResponse;
import com.example.bookrental.repository.*;
import com.example.bookrental.security.AuthorizationService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DashboardService {
    private final UserRepository users; private final UserRoleRepository userRoles; private final BookListingRepository books;
    private final BorrowRequestRepository requests; private final LoanHistoryRepository loans; private final AuthorizationService authorization;
    private final DtoMapper mapper; private final Clock clock;
    public DashboardService(UserRepository users, UserRoleRepository userRoles, BookListingRepository books,
                            BorrowRequestRepository requests, LoanHistoryRepository loans, AuthorizationService authorization,
                            DtoMapper mapper, Clock clock) {
        this.users = users; this.userRoles = userRoles; this.books = books; this.requests = requests; this.loans = loans;
        this.authorization = authorization; this.mapper = mapper; this.clock = clock;
    }
    @Transactional(readOnly = true)
    public DashboardResponse get(Long adminId) {
        authorization.requireRole(adminId, RoleName.ADMIN);
        return new DashboardResponse(users.count(), userRoles.countUsersByRole(RoleName.BORROWER), userRoles.countUsersByRole(RoleName.LENDER),
                books.count(), books.countByStatus(BookStatus.PENDING), books.countByStatus(BookStatus.APPROVED), requests.count(),
                loans.countByStatusIn(List.of(LoanStatus.LOANED, LoanStatus.OVERDUE)), loans.countByStatus(LoanStatus.RETURNED),
                loans.countOverdue(LocalDateTime.now(clock)), books.findTop5ByOrderByCreatedAtDesc().stream().map(mapper::book).toList(),
                requests.findTop5ByOrderByRequestedAtDesc().stream().map(mapper::borrowRequest).toList());
    }
}
