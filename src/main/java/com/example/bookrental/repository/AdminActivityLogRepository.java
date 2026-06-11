package com.example.bookrental.repository;
import com.example.bookrental.domain.AdminActivityLog;
import org.springframework.data.jpa.repository.JpaRepository;
public interface AdminActivityLogRepository extends JpaRepository<AdminActivityLog, Long> {}
