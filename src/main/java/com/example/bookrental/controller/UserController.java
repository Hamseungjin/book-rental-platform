package com.example.bookrental.controller;

import com.example.bookrental.dto.UserDtos;
import com.example.bookrental.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserService service;
    public UserController(UserService service) { this.service = service; }
    @PostMapping @ResponseStatus(HttpStatus.CREATED)
    public UserDtos.Response create(@Valid @RequestBody UserDtos.CreateRequest request) { return service.create(request); }
    @PostMapping("/{userId}/roles")
    public UserDtos.Response addRoles(@PathVariable Long userId, @Valid @RequestBody UserDtos.AddRolesRequest request) { return service.addRoles(userId, request); }
    @GetMapping("/{userId}")
    public UserDtos.Response get(@PathVariable Long userId) { return service.get(userId); }
}
