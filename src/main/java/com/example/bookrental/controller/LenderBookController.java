package com.example.bookrental.controller;

import com.example.bookrental.dto.BookDtos;
import com.example.bookrental.service.BookService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/lender/books")
public class LenderBookController {
    private final BookService service;
    public LenderBookController(BookService service) { this.service = service; }
    // TODO(security): JWT 적용 후 X-User-Id 대신 인증 Principal에서 사용자 ID를 가져옵니다.
    @PostMapping @ResponseStatus(HttpStatus.CREATED)
    public BookDtos.Response create(@RequestHeader("X-User-Id") Long lenderId, @Valid @RequestBody BookDtos.UpsertRequest request) {
        return service.create(lenderId, request);
    }
    @GetMapping
    public List<BookDtos.Response> list(@RequestHeader("X-User-Id") Long lenderId) { return service.lenderBooks(lenderId); }
    @PatchMapping("/{bookId}")
    public BookDtos.Response update(@RequestHeader("X-User-Id") Long lenderId, @PathVariable Long bookId,
                                    @Valid @RequestBody BookDtos.UpsertRequest request) { return service.update(lenderId, bookId, request); }
}
