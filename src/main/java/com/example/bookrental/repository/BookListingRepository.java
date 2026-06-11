package com.example.bookrental.repository;
import com.example.bookrental.domain.BookListing;
import com.example.bookrental.domain.enums.BookStatus;
import jakarta.persistence.LockModeType;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
public interface BookListingRepository extends JpaRepository<BookListing, Long> {
    List<BookListing> findAllByLenderIdOrderByCreatedAtDesc(Long lenderId);
    List<BookListing> findAllByStatusOrderByCreatedAtDesc(BookStatus status);
    Optional<BookListing> findByIdAndStatus(Long id, BookStatus status);
    long countByStatus(BookStatus status);
    List<BookListing> findTop5ByOrderByCreatedAtDesc();
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select b from BookListing b where b.id = :id")
    Optional<BookListing> findByIdForUpdate(@Param("id") Long id);
}
