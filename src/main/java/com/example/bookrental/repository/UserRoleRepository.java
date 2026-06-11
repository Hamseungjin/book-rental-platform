package com.example.bookrental.repository;
import com.example.bookrental.domain.UserRole;
import com.example.bookrental.domain.enums.RoleName;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
public interface UserRoleRepository extends JpaRepository<UserRole, Long> {
    boolean existsByUserIdAndRoleName(Long userId, RoleName roleName);
    List<UserRole> findAllByUserId(Long userId);
    @Query("select count(distinct ur.user.id) from UserRole ur where ur.role.name = :role")
    long countUsersByRole(@Param("role") RoleName role);
}
