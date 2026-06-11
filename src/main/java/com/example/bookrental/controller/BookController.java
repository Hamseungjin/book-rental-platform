package com.example.bookrental.controller;

import com.example.bookrental.dto.BookDtos;
import com.example.bookrental.service.BookService;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/books")
public class BookController {
    private final BookService service;
    public BookController(BookService service) { this.service = service; }
    @GetMapping public List<BookDtos.Response> list() { return service.approvedBooks(); }
    @GetMapping("/{bookId}") public BookDtos.Response get(@PathVariable Long bookId) { return service.approvedBook(bookId); }
}
