package com.example.bookrental.dto;

import java.util.List;

public record DashboardResponse(long totalUsers, long borrowerUsers, long lenderUsers,
                                long totalBooks, long pendingBooks, long approvedBooks,
                                long totalBorrowRequests, long activeLoans, long returnedLoans, long overdueLoans,
                                List<BookDtos.Response> recentBooks,
                                List<BorrowRequestDtos.Response> recentBorrowRequests) {}
