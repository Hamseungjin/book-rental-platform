package com.example.bookrental.domain;

import com.example.bookrental.domain.enums.BorrowRequestStatus;
import com.example.bookrental.exception.BusinessException;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "borrow_requests", indexes = {
        @Index(name = "idx_requests_status_requested", columnList = "status,requested_at"),
        @Index(name = "idx_requests_borrower", columnList = "borrower_id"),
        @Index(name = "idx_requests_book", columnList = "book_listing_id")
})
public class BorrowRequest extends BaseEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "borrower_id", nullable = false, foreignKey = @ForeignKey(name = "fk_requests_borrower"))
    private User borrower;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_listing_id", nullable = false, foreignKey = @ForeignKey(name = "fk_requests_book"))
    private BookListing bookListing;
    @Column(nullable = false)
    private int quantity;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 30)
    private BorrowRequestStatus status = BorrowRequestStatus.REQUESTED;
    @Column(name = "requested_at", nullable = false)
    private LocalDateTime requestedAt;
    @Column(name = "approved_at") private LocalDateTime approvedAt;
    @Column(name = "rejected_at") private LocalDateTime rejectedAt;
    @Column(name = "canceled_at") private LocalDateTime canceledAt;
    @Version private long version;

    protected BorrowRequest() {}
    public BorrowRequest(User borrower, BookListing listing, int quantity, LocalDateTime requestedAt) {
        if (quantity < 1) throw new BusinessException("대여 요청 수량은 1 이상이어야 합니다.");
        this.borrower = borrower; this.bookListing = listing; this.quantity = quantity; this.requestedAt = requestedAt;
    }
    public void approve(LocalDateTime now) { ensureRequested(); status = BorrowRequestStatus.APPROVED; approvedAt = now; }
    public void reject(LocalDateTime now) { ensureRequested(); status = BorrowRequestStatus.REJECTED; rejectedAt = now; }
    public void cancel(LocalDateTime now) { ensureRequested(); status = BorrowRequestStatus.CANCELED; canceledAt = now; }
    private void ensureRequested() {
        if (status != BorrowRequestStatus.REQUESTED) throw new BusinessException("요청 대기 상태에서만 처리할 수 있습니다.");
    }
    public Long getId() { return id; }
    public User getBorrower() { return borrower; }
    public BookListing getBookListing() { return bookListing; }
    public int getQuantity() { return quantity; }
    public BorrowRequestStatus getStatus() { return status; }
    public LocalDateTime getRequestedAt() { return requestedAt; }
    public LocalDateTime getApprovedAt() { return approvedAt; }
    public LocalDateTime getRejectedAt() { return rejectedAt; }
    public LocalDateTime getCanceledAt() { return canceledAt; }
}
