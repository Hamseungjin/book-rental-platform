package com.example.bookrental.controller;

import com.example.bookrental.dto.BorrowRequestDtos;
import com.example.bookrental.service.BorrowRequestService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/borrow-requests")
public class BorrowRequestController {
    private final BorrowRequestService service;
    public BorrowRequestController(BorrowRequestService service) { this.service = service; }
    // TODO(security): JWT 적용 후 X-User-Id 대신 인증 Principal을 사용합니다.
    @PostMapping @ResponseStatus(HttpStatus.CREATED)
    public BorrowRequestDtos.Response create(@RequestHeader("X-User-Id") Long borrowerId,
                                             @Valid @RequestBody BorrowRequestDtos.CreateRequest request) {
        return service.create(borrowerId, request);
    }
    @GetMapping("/me")
    public List<BorrowRequestDtos.Response> mine(@RequestHeader("X-User-Id") Long borrowerId) { return service.mine(borrowerId); }
}
