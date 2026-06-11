package com.example.bookrental.security;

import com.example.bookrental.domain.enums.RoleName;
import com.example.bookrental.exception.ForbiddenException;
import com.example.bookrental.repository.UserRoleRepository;
import org.springframework.stereotype.Component;

/**
 * JWT/Spring Security 도입 전의 권한 경계입니다. 현재는 컨트롤러가 전달한 사용자 ID를 검사합니다.
 * 추후 SecurityContext 기반 CurrentUserProvider로 교체하고 @PreAuthorize를 적용합니다.
 */
@Component
public class AuthorizationService {
    private final UserRoleRepository userRoleRepository;
    public AuthorizationService(UserRoleRepository userRoleRepository) { this.userRoleRepository = userRoleRepository; }
    public void requireRole(Long userId, RoleName role) {
        if (!userRoleRepository.existsByUserIdAndRoleName(userId, role)) throw new ForbiddenException(role + " 권한이 필요합니다.");
    }
}
