package com.example.bookrental.domain;

import com.example.bookrental.domain.enums.BookFormat;
import com.example.bookrental.domain.enums.BookStatus;
import com.example.bookrental.exception.BusinessException;
import jakarta.persistence.*;

@Entity
@Table(name = "book_listings", indexes = {
        @Index(name = "idx_books_status_created", columnList = "status,created_at"),
        @Index(name = "idx_books_lender", columnList = "lender_id")
})
public class BookListing extends BaseEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "lender_id", nullable = false, foreignKey = @ForeignKey(name = "fk_books_lender"))
    private User lender;
    @Column(nullable = false, length = 200)
    private String title;
    @Column(nullable = false, length = 150)
    private String author;
    @Column(nullable = false, length = 100)
    private String category;
    @Column(nullable = false, columnDefinition = "TEXT")
    private String description;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 30)
    private BookFormat format;
    @Column(name = "total_quantity", nullable = false)
    private int totalQuantity;
    @Column(name = "available_quantity", nullable = false)
    private int availableQuantity;
    @Column(name = "default_loan_days", nullable = false)
    private int defaultLoanDays;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 30)
    private BookStatus status = BookStatus.PENDING;
    @Column(name = "rejection_memo", length = 500)
    private String rejectionMemo;
    @Version
    private long version;

    protected BookListing() {}
    public BookListing(User lender, String title, String author, String category, String description,
                       BookFormat format, int totalQuantity, int availableQuantity, int defaultLoanDays) {
        validateQuantities(totalQuantity, availableQuantity);
        if (defaultLoanDays < 1) throw new BusinessException("기본 대여 기간은 1일 이상이어야 합니다.");
        this.lender = lender; this.title = title; this.author = author; this.category = category;
        this.description = description; this.format = format; this.totalQuantity = totalQuantity;
        this.availableQuantity = availableQuantity; this.defaultLoanDays = defaultLoanDays;
    }
    public void update(String title, String author, String category, String description, BookFormat format,
                       int totalQuantity, int availableQuantity, int defaultLoanDays) {
        if (status != BookStatus.PENDING && status != BookStatus.REJECTED)
            throw new BusinessException("승인 대기 또는 거절 상태의 책만 수정할 수 있습니다.");
        validateQuantities(totalQuantity, availableQuantity);
        if (defaultLoanDays < 1) throw new BusinessException("기본 대여 기간은 1일 이상이어야 합니다.");
        this.title = title; this.author = author; this.category = category; this.description = description;
        this.format = format; this.totalQuantity = totalQuantity; this.availableQuantity = availableQuantity;
        this.defaultLoanDays = defaultLoanDays; this.status = BookStatus.PENDING; this.rejectionMemo = null;
    }
    private static void validateQuantities(int total, int available) {
        if (total < 1 || available < 0 || available > total)
            throw new BusinessException("수량은 총 수량 1 이상, 대여 가능 수량 0 이상이며 총 수량 이하여야 합니다.");
    }
    public void approve() {
        if (status != BookStatus.PENDING) throw new BusinessException("승인 대기 상태의 책만 승인할 수 있습니다.");
        status = BookStatus.APPROVED; rejectionMemo = null;
    }
    public void reject(String memo) {
        if (status != BookStatus.PENDING) throw new BusinessException("승인 대기 상태의 책만 거절할 수 있습니다.");
        status = BookStatus.REJECTED; rejectionMemo = memo;
    }
    public void ensureApproved() {
        if (status != BookStatus.APPROVED) throw new BusinessException("승인된 책만 대여할 수 있습니다.");
    }
    public void decreaseAvailableQuantity(int quantity) {
        if (quantity < 1 || availableQuantity < quantity) throw new BusinessException("대여 가능한 책 수량이 부족합니다.");
        availableQuantity -= quantity;
    }
    public void increaseAvailableQuantity(int quantity) {
        if (quantity < 1 || availableQuantity + quantity > totalQuantity)
            throw new BusinessException("반납 후 대여 가능 수량이 총 수량을 초과할 수 없습니다.");
        availableQuantity += quantity;
    }
    public Long getId() { return id; }
    public User getLender() { return lender; }
    public String getTitle() { return title; }
    public String getAuthor() { return author; }
    public String getCategory() { return category; }
    public String getDescription() { return description; }
    public BookFormat getFormat() { return format; }
    public int getTotalQuantity() { return totalQuantity; }
    public int getAvailableQuantity() { return availableQuantity; }
    public int getDefaultLoanDays() { return defaultLoanDays; }
    public BookStatus getStatus() { return status; }
    public String getRejectionMemo() { return rejectionMemo; }
}
