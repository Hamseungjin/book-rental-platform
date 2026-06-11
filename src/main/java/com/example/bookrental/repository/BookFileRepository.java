package com.example.bookrental.repository;
import com.example.bookrental.domain.BookFile;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
public interface BookFileRepository extends JpaRepository<BookFile, Long> { Optional<BookFile> findByBookListingId(Long listingId); void deleteByBookListingId(Long listingId); }
