package com.example.bookrental.repository;
import com.example.bookrental.domain.BorrowRequest;
import com.example.bookrental.domain.enums.BorrowRequestStatus;
import jakarta.persistence.LockModeType;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
public interface BorrowRequestRepository extends JpaRepository<BorrowRequest, Long> {
    List<BorrowRequest> findAllByBorrowerIdOrderByRequestedAtDesc(Long borrowerId);
    List<BorrowRequest> findAllByOrderByRequestedAtDesc();
    long countByStatus(BorrowRequestStatus status);
    List<BorrowRequest> findTop5ByOrderByRequestedAtDesc();
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select br from BorrowRequest br where br.id = :id")
    Optional<BorrowRequest> findByIdForUpdate(@Param("id") Long id);
}
