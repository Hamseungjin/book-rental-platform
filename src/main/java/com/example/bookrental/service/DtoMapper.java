package com.example.bookrental.service;

import com.example.bookrental.domain.*;
import com.example.bookrental.dto.*;
import com.example.bookrental.repository.BookFileRepository;
import org.springframework.stereotype.Component;

@Component
public class DtoMapper {
    private final BookFileRepository bookFileRepository;
    public DtoMapper(BookFileRepository bookFileRepository) { this.bookFileRepository = bookFileRepository; }
    public BookDtos.Response book(BookListing b) {
        BookDtos.FileResponse file = bookFileRepository.findByBookListingId(b.getId())
                .map(f -> new BookDtos.FileResponse(f.getId(), f.getOriginalFilename(), f.getStoredFileUrl(), f.getMimeType(), f.getFileSize()))
                .orElse(null);
        return new BookDtos.Response(b.getId(), b.getLender().getId(), b.getLender().getName(), b.getTitle(), b.getAuthor(), b.getCategory(),
                b.getDescription(), b.getFormat(), b.getTotalQuantity(), b.getAvailableQuantity(), b.getDefaultLoanDays(), b.getStatus(),
                b.getRejectionMemo(), file, b.getCreatedAt(), b.getUpdatedAt());
    }
    public BorrowRequestDtos.Response borrowRequest(BorrowRequest r) {
        return new BorrowRequestDtos.Response(r.getId(), r.getBorrower().getId(), r.getBorrower().getName(), r.getBookListing().getId(),
                r.getBookListing().getTitle(), r.getQuantity(), r.getStatus(), r.getRequestedAt(), r.getApprovedAt(), r.getRejectedAt(), r.getCanceledAt());
    }
    public LoanDtos.Response loan(LoanHistory l) {
        return new LoanDtos.Response(l.getId(), l.getBorrowRequest().getId(), l.getBorrower().getId(), l.getBorrower().getName(),
                l.getLender().getId(), l.getLender().getName(), l.getBookListing().getId(), l.getBookListing().getTitle(), l.getQuantity(),
                l.getLoanedAt(), l.getDueAt(), l.getReturnedAt(), l.getStatus());
    }
}
