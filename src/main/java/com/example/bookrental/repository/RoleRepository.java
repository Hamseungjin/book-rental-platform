package com.example.bookrental.repository;
import com.example.bookrental.domain.Role;
import com.example.bookrental.domain.enums.RoleName;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
public interface RoleRepository extends JpaRepository<Role, Long> { Optional<Role> findByName(RoleName name); }
