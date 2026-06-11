package com.example.bookrental.service;

import com.example.bookrental.domain.*;
import com.example.bookrental.domain.enums.*;
import com.example.bookrental.dto.BorrowRequestDtos;
import com.example.bookrental.exception.*;
import com.example.bookrental.repository.*;
import com.example.bookrental.security.AuthorizationService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BorrowRequestService {
    private final BorrowRequestRepository requests; private final BookListingRepository books; private final UserRepository users;
    private final AuthorizationService authorization; private final DtoMapper mapper; private final Clock clock;
    public BorrowRequestService(BorrowRequestRepository requests, BookListingRepository books, UserRepository users,
                                AuthorizationService authorization, DtoMapper mapper, Clock clock) {
        this.requests = requests; this.books = books; this.users = users; this.authorization = authorization; this.mapper = mapper; this.clock = clock;
    }
    @Transactional
    public BorrowRequestDtos.Response create(Long borrowerId, BorrowRequestDtos.CreateRequest request) {
        authorization.requireRole(borrowerId, RoleName.BORROWER);
        User borrower = users.findById(borrowerId).orElseThrow(() -> new NotFoundException("사용자", borrowerId));
        BookListing book = books.findByIdAndStatus(request.bookListingId(), BookStatus.APPROVED)
                .orElseThrow(() -> new NotFoundException("승인된 책", request.bookListingId()));
        if (book.getLender().getId().equals(borrowerId)) throw new BusinessException("본인이 등록한 책은 대여할 수 없습니다.");
        if (book.getAvailableQuantity() < request.quantity()) throw new BusinessException("현재 대여 가능한 수량보다 많이 요청할 수 없습니다.");
        return mapper.borrowRequest(requests.save(new BorrowRequest(borrower, book, request.quantity(), LocalDateTime.now(clock))));
    }
    @Transactional(readOnly = true)
    public List<BorrowRequestDtos.Response> mine(Long borrowerId) {
        authorization.requireRole(borrowerId, RoleName.BORROWER);
        return requests.findAllByBorrowerIdOrderByRequestedAtDesc(borrowerId).stream().map(mapper::borrowRequest).toList();
    }
}
