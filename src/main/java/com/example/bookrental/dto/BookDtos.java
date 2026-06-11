package com.example.bookrental.dto;

import com.example.bookrental.domain.enums.BookFormat;
import com.example.bookrental.domain.enums.BookStatus;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.time.LocalDateTime;

public final class BookDtos {
    private BookDtos() {}
    public record FileRequest(@NotBlank String originalFilename, @NotBlank String storedFileUrl,
                              @NotBlank String mimeType, @Positive long fileSize) {}
    public record UpsertRequest(@NotBlank @Size(max=200) String title, @NotBlank @Size(max=150) String author,
                                @NotBlank @Size(max=100) String category, @NotBlank String description,
                                @NotNull BookFormat format, @Min(1) int totalQuantity,
                                @Min(0) int availableQuantity, @Min(1) int defaultLoanDays,
                                @Valid FileRequest file) {}
    public record FileResponse(Long id, String originalFilename, String storedFileUrl, String mimeType, long fileSize) {}
    public record Response(Long id, Long lenderId, String lenderName, String title, String author, String category,
                           String description, BookFormat format, int totalQuantity, int availableQuantity,
                           int defaultLoanDays, BookStatus status, String rejectionMemo, FileResponse file,
                           LocalDateTime createdAt, LocalDateTime updatedAt) {}
    public record RejectRequest(@NotBlank @Size(max=500) String memo) {}
}
