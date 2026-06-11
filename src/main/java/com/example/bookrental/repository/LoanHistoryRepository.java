package com.example.bookrental.repository;
import com.example.bookrental.domain.LoanHistory;
import com.example.bookrental.domain.enums.LoanStatus;
import jakarta.persistence.LockModeType;
import java.time.LocalDateTime;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
public interface LoanHistoryRepository extends JpaRepository<LoanHistory, Long> {
    List<LoanHistory> findAllByOrderByLoanedAtDesc();
    List<LoanHistory> findAllByStatusInOrderByDueAtAsc(Collection<LoanStatus> statuses);
    @Query("select l from LoanHistory l where l.status = com.example.bookrental.domain.enums.LoanStatus.OVERDUE or (l.status = com.example.bookrental.domain.enums.LoanStatus.LOANED and l.dueAt < :now) order by l.dueAt")
    List<LoanHistory> findOverdue(@Param("now") LocalDateTime now);
    @Query("select count(l) from LoanHistory l where l.status = com.example.bookrental.domain.enums.LoanStatus.OVERDUE or (l.status = com.example.bookrental.domain.enums.LoanStatus.LOANED and l.dueAt < :now)")
    long countOverdue(@Param("now") LocalDateTime now);
    long countByStatus(LoanStatus status);
    long countByStatusIn(Collection<LoanStatus> statuses);
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select l from LoanHistory l where l.id = :id")
    Optional<LoanHistory> findByIdForUpdate(@Param("id") Long id);
}
