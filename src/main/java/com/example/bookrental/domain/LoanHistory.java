package com.example.bookrental.domain;

import com.example.bookrental.domain.enums.LoanStatus;
import com.example.bookrental.exception.BusinessException;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "loan_history", uniqueConstraints = @UniqueConstraint(name = "uk_loans_request", columnNames = "borrow_request_id"), indexes = {
        @Index(name = "idx_loans_status_due", columnList = "status,due_at"),
        @Index(name = "idx_loans_borrower", columnList = "borrower_id"),
        @Index(name = "idx_loans_lender", columnList = "lender_id")
})
public class LoanHistory extends BaseEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "borrow_request_id", nullable = false, foreignKey = @ForeignKey(name = "fk_loans_request"))
    private BorrowRequest borrowRequest;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "borrower_id", nullable = false, foreignKey = @ForeignKey(name = "fk_loans_borrower"))
    private User borrower;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "lender_id", nullable = false, foreignKey = @ForeignKey(name = "fk_loans_lender"))
    private User lender;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_listing_id", nullable = false, foreignKey = @ForeignKey(name = "fk_loans_book"))
    private BookListing bookListing;
    @Column(nullable = false) private int quantity;
    @Column(name = "loaned_at", nullable = false) private LocalDateTime loanedAt;
    @Column(name = "due_at", nullable = false) private LocalDateTime dueAt;
    @Column(name = "returned_at") private LocalDateTime returnedAt;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 30)
    private LoanStatus status = LoanStatus.LOANED;
    @Version private long version;

    protected LoanHistory() {}
    public LoanHistory(BorrowRequest request, LocalDateTime loanedAt, LocalDateTime dueAt) {
        this.borrowRequest = request; this.borrower = request.getBorrower(); this.lender = request.getBookListing().getLender();
        this.bookListing = request.getBookListing(); this.quantity = request.getQuantity(); this.loanedAt = loanedAt; this.dueAt = dueAt;
    }
    public void returnBook(LocalDateTime now) {
        if (status != LoanStatus.LOANED && status != LoanStatus.OVERDUE) throw new BusinessException("대출 중이거나 연체된 건만 반납할 수 있습니다.");
        status = LoanStatus.RETURNED; returnedAt = now;
    }
    public void markOverdue() {
        if (status == LoanStatus.LOANED) status = LoanStatus.OVERDUE;
    }
    public Long getId() { return id; }
    public BorrowRequest getBorrowRequest() { return borrowRequest; }
    public User getBorrower() { return borrower; }
    public User getLender() { return lender; }
    public BookListing getBookListing() { return bookListing; }
    public int getQuantity() { return quantity; }
    public LocalDateTime getLoanedAt() { return loanedAt; }
    public LocalDateTime getDueAt() { return dueAt; }
    public LocalDateTime getReturnedAt() { return returnedAt; }
    public LoanStatus getStatus() { return status; }
}
