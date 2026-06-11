package com.example.bookrental.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "book_files", uniqueConstraints = @UniqueConstraint(name = "uk_book_files_listing", columnNames = "book_listing_id"))
public class BookFile extends BaseEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_listing_id", nullable = false, foreignKey = @ForeignKey(name = "fk_book_files_listing"))
    private BookListing bookListing;
    @Column(name = "original_filename", nullable = false, length = 255)
    private String originalFilename;
    @Column(name = "stored_file_url", nullable = false, length = 1000)
    private String storedFileUrl;
    @Column(name = "mime_type", nullable = false, length = 100)
    private String mimeType;
    @Column(name = "file_size", nullable = false)
    private long fileSize;

    protected BookFile() {}
    public BookFile(BookListing listing, String originalFilename, String storedFileUrl, String mimeType, long fileSize) {
        this.bookListing = listing; this.originalFilename = originalFilename; this.storedFileUrl = storedFileUrl;
        this.mimeType = mimeType; this.fileSize = fileSize;
    }
    public void update(String originalFilename, String storedFileUrl, String mimeType, long fileSize) {
        this.originalFilename = originalFilename; this.storedFileUrl = storedFileUrl; this.mimeType = mimeType; this.fileSize = fileSize;
    }
    public Long getId() { return id; }
    public String getOriginalFilename() { return originalFilename; }
    public String getStoredFileUrl() { return storedFileUrl; }
    public String getMimeType() { return mimeType; }
    public long getFileSize() { return fileSize; }
}
