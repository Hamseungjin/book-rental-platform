package com.example.bookrental.dto;

import com.example.bookrental.domain.enums.RoleName;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import java.time.LocalDateTime;
import java.util.Set;

public final class UserDtos {
    private UserDtos() {}
    public record CreateRequest(@NotBlank String name, @NotBlank @Email String email, @NotBlank String password) {}
    public record AddRolesRequest(@NotEmpty Set<RoleName> roles) {}
    public record Response(Long id, String name, String email, boolean active, Set<RoleName> roles,
                           LocalDateTime createdAt, LocalDateTime updatedAt) {}
}
