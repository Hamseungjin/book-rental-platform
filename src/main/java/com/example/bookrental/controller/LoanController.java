package com.example.bookrental.controller;

import com.example.bookrental.dto.LoanDtos;
import com.example.bookrental.service.LoanService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/loans")
public class LoanController {
    private final LoanService service;
    public LoanController(LoanService service) { this.service = service; }
    @PatchMapping("/{loanId}/return")
    public LoanDtos.Response returnBook(@RequestHeader("X-User-Id") Long actorId, @PathVariable Long loanId) {
        return service.returnBook(actorId, loanId);
    }
}
