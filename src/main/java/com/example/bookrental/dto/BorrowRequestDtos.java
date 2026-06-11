package com.example.bookrental.dto;

import com.example.bookrental.domain.enums.BorrowRequestStatus;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public final class BorrowRequestDtos {
    private BorrowRequestDtos() {}
    public record CreateRequest(@NotNull Long bookListingId, @Min(1) int quantity) {}
    public record RejectRequest(String memo) {}
    public record Response(Long id, Long borrowerId, String borrowerName, Long bookListingId, String bookTitle,
                           int quantity, BorrowRequestStatus status, LocalDateTime requestedAt,
                           LocalDateTime approvedAt, LocalDateTime rejectedAt, LocalDateTime canceledAt) {}
}
