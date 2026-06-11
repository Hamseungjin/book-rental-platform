package com.example.bookrental.dto;

import com.example.bookrental.domain.enums.LoanStatus;
import java.time.LocalDateTime;

public final class LoanDtos {
    private LoanDtos() {}
    public record Response(Long id, Long borrowRequestId, Long borrowerId, String borrowerName,
                           Long lenderId, String lenderName, Long bookListingId, String bookTitle,
                           int quantity, LocalDateTime loanedAt, LocalDateTime dueAt,
                           LocalDateTime returnedAt, LoanStatus status) {}
}
