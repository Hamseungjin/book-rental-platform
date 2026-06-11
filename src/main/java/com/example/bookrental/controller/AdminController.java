package com.example.bookrental.controller;

import com.example.bookrental.dto.*;
import com.example.bookrental.service.*;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin")
public class AdminController {
    private final AdminService adminService; private final DashboardService dashboardService;
    public AdminController(AdminService adminService, DashboardService dashboardService) {
        this.adminService = adminService; this.dashboardService = dashboardService;
    }
    // TODO(security): Spring Security 적용 시 @PreAuthorize("hasRole('ADMIN')")와 SecurityContext 기반 ID 조회로 교체합니다.
    @GetMapping("/books/pending")
    public List<BookDtos.Response> pendingBooks(@RequestHeader("X-Admin-Id") Long adminId) { return adminService.pendingBooks(adminId); }
    @PatchMapping("/books/{bookId}/approve")
    public BookDtos.Response approveBook(@RequestHeader("X-Admin-Id") Long adminId, @PathVariable Long bookId) { return adminService.approveBook(adminId, bookId); }
    @PatchMapping("/books/{bookId}/reject")
    public BookDtos.Response rejectBook(@RequestHeader("X-Admin-Id") Long adminId, @PathVariable Long bookId,
                                        @Valid @RequestBody BookDtos.RejectRequest request) { return adminService.rejectBook(adminId, bookId, request.memo()); }
    @GetMapping("/borrow-requests")
    public List<BorrowRequestDtos.Response> requests(@RequestHeader("X-Admin-Id") Long adminId) { return adminService.allRequests(adminId); }
    @PatchMapping("/borrow-requests/{requestId}/approve")
    public LoanDtos.Response approveRequest(@RequestHeader("X-Admin-Id") Long adminId, @PathVariable Long requestId) {
        return adminService.approveBorrowRequest(adminId, requestId);
    }
    @PatchMapping("/borrow-requests/{requestId}/reject")
    public BorrowRequestDtos.Response rejectRequest(@RequestHeader("X-Admin-Id") Long adminId, @PathVariable Long requestId,
                                                     @RequestBody(required = false) BorrowRequestDtos.RejectRequest request) {
        return adminService.rejectBorrowRequest(adminId, requestId, request == null ? null : request.memo());
    }
    @GetMapping("/loans")
    public List<LoanDtos.Response> loans(@RequestHeader("X-Admin-Id") Long adminId) { return adminService.loans(adminId); }
    @GetMapping("/loans/overdue")
    public List<LoanDtos.Response> overdue(@RequestHeader("X-Admin-Id") Long adminId) { return adminService.overdueLoans(adminId); }
    @GetMapping("/dashboard")
    public DashboardResponse dashboard(@RequestHeader("X-Admin-Id") Long adminId) { return dashboardService.get(adminId); }
}
