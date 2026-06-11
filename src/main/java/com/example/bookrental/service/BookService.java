package com.example.bookrental.service;

import com.example.bookrental.domain.*;
import com.example.bookrental.domain.enums.*;
import com.example.bookrental.dto.BookDtos;
import com.example.bookrental.exception.*;
import com.example.bookrental.repository.*;
import com.example.bookrental.security.AuthorizationService;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BookService {
    private final BookListingRepository books; private final BookFileRepository files; private final UserRepository users;
    private final AuthorizationService authorization; private final DtoMapper mapper;
    public BookService(BookListingRepository books, BookFileRepository files, UserRepository users, AuthorizationService authorization, DtoMapper mapper) {
        this.books = books; this.files = files; this.users = users; this.authorization = authorization; this.mapper = mapper;
    }
    @Transactional
    public BookDtos.Response create(Long lenderId, BookDtos.UpsertRequest request) {
        authorization.requireRole(lenderId, RoleName.LENDER); validateFile(request);
        User lender = users.findById(lenderId).orElseThrow(() -> new NotFoundException("사용자", lenderId));
        BookListing listing = books.save(new BookListing(lender, request.title(), request.author(), request.category(), request.description(),
                request.format(), request.totalQuantity(), request.availableQuantity(), request.defaultLoanDays()));
        saveFile(listing, request.file());
        return mapper.book(listing);
    }
    @Transactional(readOnly = true)
    public List<BookDtos.Response> lenderBooks(Long lenderId) {
        authorization.requireRole(lenderId, RoleName.LENDER);
        return books.findAllByLenderIdOrderByCreatedAtDesc(lenderId).stream().map(mapper::book).toList();
    }
    @Transactional
    public BookDtos.Response update(Long lenderId, Long bookId, BookDtos.UpsertRequest request) {
        authorization.requireRole(lenderId, RoleName.LENDER); validateFile(request);
        BookListing listing = books.findById(bookId).orElseThrow(() -> new NotFoundException("책", bookId));
        if (!listing.getLender().getId().equals(lenderId)) throw new ForbiddenException("본인이 등록한 책만 수정할 수 있습니다.");
        listing.update(request.title(), request.author(), request.category(), request.description(), request.format(),
                request.totalQuantity(), request.availableQuantity(), request.defaultLoanDays());
        files.findByBookListingId(bookId).ifPresent(files::delete);
        saveFile(listing, request.file());
        return mapper.book(listing);
    }
    @Transactional(readOnly = true)
    public List<BookDtos.Response> approvedBooks() { return books.findAllByStatusOrderByCreatedAtDesc(BookStatus.APPROVED).stream().map(mapper::book).toList(); }
    @Transactional(readOnly = true)
    public BookDtos.Response approvedBook(Long id) { return mapper.book(books.findByIdAndStatus(id, BookStatus.APPROVED).orElseThrow(() -> new NotFoundException("승인된 책", id))); }
    private void validateFile(BookDtos.UpsertRequest request) {
        if (request.availableQuantity() > request.totalQuantity()) throw new BusinessException("대여 가능 수량은 총 수량을 초과할 수 없습니다.");
        if (request.format() == BookFormat.PDF && request.file() == null) throw new BusinessException("PDF 책은 파일 정보가 필요합니다.");
        if (request.format() != BookFormat.PDF && request.file() != null) throw new BusinessException("실물책에는 PDF 파일 정보를 등록할 수 없습니다.");
        if (request.file() != null && !"application/pdf".equalsIgnoreCase(request.file().mimeType())) throw new BusinessException("PDF MIME type은 application/pdf여야 합니다.");
    }
    private void saveFile(BookListing listing, BookDtos.FileRequest file) {
        if (file != null) files.save(new BookFile(listing, file.originalFilename(), file.storedFileUrl(), file.mimeType(), file.fileSize()));
    }
}
