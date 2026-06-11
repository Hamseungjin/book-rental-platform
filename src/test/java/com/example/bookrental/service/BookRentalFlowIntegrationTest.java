package com.example.bookrental.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.example.bookrental.domain.enums.*;
import com.example.bookrental.dto.*;
import com.example.bookrental.exception.BusinessException;
import com.example.bookrental.repository.*;
import java.util.Set;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class BookRentalFlowIntegrationTest {
    @Autowired UserService userService;
    @Autowired BookService bookService;
    @Autowired BorrowRequestService borrowRequestService;
    @Autowired AdminService adminService;
    @Autowired LoanService loanService;
    @Autowired BookListingRepository bookRepository;
    @Autowired BorrowRequestRepository requestRepository;
    @Autowired LoanHistoryRepository loanRepository;
    @Autowired AdminActivityLogRepository logRepository;
    @Autowired BookFileRepository fileRepository;
    @Autowired UserRoleRepository userRoleRepository;
    @Autowired UserRepository userRepository;

    private Long lenderId;
    private Long borrowerId;
    private Long secondBorrowerId;
    private Long adminId;

    @BeforeEach
    void setUp() {
        logRepository.deleteAll(); loanRepository.deleteAll(); requestRepository.deleteAll(); fileRepository.deleteAll();
        bookRepository.deleteAll(); userRoleRepository.deleteAll(); userRepository.deleteAll();
        lenderId = createUser("lender", "lender@example.com", RoleName.LENDER);
        borrowerId = createUser("borrower", "borrower@example.com", RoleName.BORROWER);
        secondBorrowerId = createUser("borrower2", "borrower2@example.com", RoleName.BORROWER);
        adminId = createUser("admin", "admin@example.com", RoleName.ADMIN);
    }

    @Test
    void completeLoanLifecycleChangesInventoryAtomically() {
        BookDtos.Response book = createAndApproveBook(2);
        BorrowRequestDtos.Response request = borrowRequestService.create(borrowerId, new BorrowRequestDtos.CreateRequest(book.id(), 1));

        LoanDtos.Response loan = adminService.approveBorrowRequest(adminId, request.id());

        assertThat(loan.status()).isEqualTo(LoanStatus.LOANED);
        assertThat(bookRepository.findById(book.id()).orElseThrow().getAvailableQuantity()).isEqualTo(1);
        assertThat(requestRepository.findById(request.id()).orElseThrow().getStatus()).isEqualTo(BorrowRequestStatus.APPROVED);
        assertThat(logRepository.count()).isEqualTo(2); // 책 승인 + 대여 요청 승인

        LoanDtos.Response returned = loanService.returnBook(borrowerId, loan.id());

        assertThat(returned.status()).isEqualTo(LoanStatus.RETURNED);
        assertThat(returned.returnedAt()).isNotNull();
        assertThat(bookRepository.findById(book.id()).orElseThrow().getAvailableQuantity()).isEqualTo(2);
    }

    @Test
    void secondApprovalFailsWithoutNegativeInventoryOrPartialState() {
        BookDtos.Response book = createAndApproveBook(1);
        BorrowRequestDtos.Response first = borrowRequestService.create(borrowerId, new BorrowRequestDtos.CreateRequest(book.id(), 1));
        BorrowRequestDtos.Response second = borrowRequestService.create(secondBorrowerId, new BorrowRequestDtos.CreateRequest(book.id(), 1));
        adminService.approveBorrowRequest(adminId, first.id());

        assertThatThrownBy(() -> adminService.approveBorrowRequest(adminId, second.id()))
                .isInstanceOf(BusinessException.class)
                .hasMessageContaining("수량이 부족");

        assertThat(bookRepository.findById(book.id()).orElseThrow().getAvailableQuantity()).isZero();
        assertThat(requestRepository.findById(second.id()).orElseThrow().getStatus()).isEqualTo(BorrowRequestStatus.REQUESTED);
        assertThat(loanRepository.count()).isEqualTo(1);
    }

    private Long createUser(String name, String email, RoleName role) {
        UserDtos.Response user = userService.create(new UserDtos.CreateRequest(name, email, "password123!"));
        userService.addRoles(user.id(), new UserDtos.AddRolesRequest(Set.of(role)));
        return user.id();
    }

    private BookDtos.Response createAndApproveBook(int quantity) {
        BookDtos.Response pending = bookService.create(lenderId, new BookDtos.UpsertRequest(
                "도메인 주도 설계", "Eric Evans", "소프트웨어", "DDD 참고서", BookFormat.PHYSICAL_BOOK,
                quantity, quantity, 14, null));
        assertThat(pending.status()).isEqualTo(BookStatus.PENDING);
        return adminService.approveBook(adminId, pending.id());
    }
}
