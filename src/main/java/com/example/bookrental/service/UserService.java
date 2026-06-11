package com.example.bookrental.service;

import com.example.bookrental.domain.*;
import com.example.bookrental.domain.enums.RoleName;
import com.example.bookrental.dto.UserDtos;
import com.example.bookrental.exception.BusinessException;
import com.example.bookrental.exception.NotFoundException;
import com.example.bookrental.repository.*;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserService {
    private final UserRepository users; private final RoleRepository roles; private final UserRoleRepository userRoles; private final PasswordEncoder encoder;
    public UserService(UserRepository users, RoleRepository roles, UserRoleRepository userRoles, PasswordEncoder encoder) {
        this.users = users; this.roles = roles; this.userRoles = userRoles; this.encoder = encoder;
    }
    @Transactional
    public UserDtos.Response create(UserDtos.CreateRequest request) {
        if (users.findByEmail(request.email()).isPresent()) throw new BusinessException("이미 사용 중인 이메일입니다.");
        User user = users.save(new User(request.name(), request.email(), encoder.encode(request.password())));
        return toResponse(user);
    }
    @Transactional
    public UserDtos.Response addRoles(Long userId, UserDtos.AddRolesRequest request) {
        User user = findUser(userId);
        for (RoleName roleName : request.roles()) {
            if (!userRoles.existsByUserIdAndRoleName(userId, roleName)) {
                Role role = roles.findByName(roleName).orElseThrow(() -> new BusinessException("역할 초기화가 필요합니다: " + roleName));
                userRoles.save(new UserRole(user, role));
            }
        }
        return toResponse(user);
    }
    @Transactional(readOnly = true)
    public UserDtos.Response get(Long userId) { return toResponse(findUser(userId)); }
    private User findUser(Long id) { return users.findById(id).orElseThrow(() -> new NotFoundException("사용자", id)); }
    private UserDtos.Response toResponse(User user) {
        Set<RoleName> roleNames = userRoles.findAllByUserId(user.getId()).stream().map(ur -> ur.getRole().getName()).collect(Collectors.toSet());
        return new UserDtos.Response(user.getId(), user.getName(), user.getEmail(), user.isActive(), roleNames, user.getCreatedAt(), user.getUpdatedAt());
    }
}
