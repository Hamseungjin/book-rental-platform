package com.example.bookrental.service;

import com.example.bookrental.domain.*;
import com.example.bookrental.domain.enums.RoleName;
import com.example.bookrental.dto.LoanDtos;
import com.example.bookrental.exception.*;
import com.example.bookrental.repository.*;
import java.time.Clock;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LoanService {
    private final LoanHistoryRepository loans; private final BookListingRepository books; private final UserRepository users;
    private final UserRoleRepository userRoles; private final DtoMapper mapper; private final Clock clock;
    public LoanService(LoanHistoryRepository loans, BookListingRepository books, UserRepository users,
                       UserRoleRepository userRoles, DtoMapper mapper, Clock clock) {
        this.loans = loans; this.books = books; this.users = users; this.userRoles = userRoles; this.mapper = mapper; this.clock = clock;
    }
    @Transactional
    public LoanDtos.Response returnBook(Long actorId, Long loanId) {
        if (!users.existsById(actorId)) throw new NotFoundException("사용자", actorId);
        LoanHistory loan = loans.findByIdForUpdate(loanId).orElseThrow(() -> new NotFoundException("대출", loanId));
        boolean admin = userRoles.existsByUserIdAndRoleName(actorId, RoleName.ADMIN);
        if (!loan.getBorrower().getId().equals(actorId) && !admin) throw new ForbiddenException("대여자 또는 운영자만 반납 처리할 수 있습니다.");
        BookListing book = books.findByIdForUpdate(loan.getBookListing().getId()).orElseThrow(() -> new NotFoundException("책", loan.getBookListing().getId()));
        loan.returnBook(LocalDateTime.now(clock));
        book.increaseAvailableQuantity(loan.getQuantity());
        return mapper.loan(loan);
    }
}
