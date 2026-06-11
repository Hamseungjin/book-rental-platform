CREATE TABLE users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_users_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE roles (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(30) NOT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_roles_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE user_roles (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_user_roles UNIQUE (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE book_listings (
    id BIGINT NOT NULL AUTO_INCREMENT,
    lender_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    format VARCHAR(30) NOT NULL,
    total_quantity INT NOT NULL,
    available_quantity INT NOT NULL,
    default_loan_days INT NOT NULL,
    status VARCHAR(30) NOT NULL,
    rejection_memo VARCHAR(500),
    version BIGINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_books_lender FOREIGN KEY (lender_id) REFERENCES users(id),
    CONSTRAINT chk_books_quantity CHECK (total_quantity >= 1 AND available_quantity >= 0 AND available_quantity <= total_quantity),
    CONSTRAINT chk_books_loan_days CHECK (default_loan_days >= 1),
    INDEX idx_books_status_created (status, created_at),
    INDEX idx_books_lender (lender_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE book_files (
    id BIGINT NOT NULL AUTO_INCREMENT,
    book_listing_id BIGINT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_file_url VARCHAR(1000) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_book_files_listing UNIQUE (book_listing_id),
    CONSTRAINT fk_book_files_listing FOREIGN KEY (book_listing_id) REFERENCES book_listings(id),
    CONSTRAINT chk_book_files_size CHECK (file_size > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE borrow_requests (
    id BIGINT NOT NULL AUTO_INCREMENT,
    borrower_id BIGINT NOT NULL,
    book_listing_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    status VARCHAR(30) NOT NULL,
    requested_at DATETIME(6) NOT NULL,
    approved_at DATETIME(6),
    rejected_at DATETIME(6),
    canceled_at DATETIME(6),
    version BIGINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_requests_borrower FOREIGN KEY (borrower_id) REFERENCES users(id),
    CONSTRAINT fk_requests_book FOREIGN KEY (book_listing_id) REFERENCES book_listings(id),
    CONSTRAINT chk_requests_quantity CHECK (quantity >= 1),
    INDEX idx_requests_status_requested (status, requested_at),
    INDEX idx_requests_borrower (borrower_id),
    INDEX idx_requests_book (book_listing_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE loan_history (
    id BIGINT NOT NULL AUTO_INCREMENT,
    borrow_request_id BIGINT NOT NULL,
    borrower_id BIGINT NOT NULL,
    lender_id BIGINT NOT NULL,
    book_listing_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    loaned_at DATETIME(6) NOT NULL,
    due_at DATETIME(6) NOT NULL,
    returned_at DATETIME(6),
    status VARCHAR(30) NOT NULL,
    version BIGINT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_loans_request UNIQUE (borrow_request_id),
    CONSTRAINT fk_loans_request FOREIGN KEY (borrow_request_id) REFERENCES borrow_requests(id),
    CONSTRAINT fk_loans_borrower FOREIGN KEY (borrower_id) REFERENCES users(id),
    CONSTRAINT fk_loans_lender FOREIGN KEY (lender_id) REFERENCES users(id),
    CONSTRAINT fk_loans_book FOREIGN KEY (book_listing_id) REFERENCES book_listings(id),
    CONSTRAINT chk_loans_quantity CHECK (quantity >= 1),
    INDEX idx_loans_status_due (status, due_at),
    INDEX idx_loans_borrower (borrower_id),
    INDEX idx_loans_lender (lender_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE admin_activity_logs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    admin_id BIGINT NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id BIGINT NOT NULL,
    memo VARCHAR(1000),
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_admin_logs_admin FOREIGN KEY (admin_id) REFERENCES users(id),
    INDEX idx_admin_logs_admin_created (admin_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO roles(name, created_at, updated_at) VALUES
('BORROWER', CURRENT_TIMESTAMP(6), CURRENT_TIMESTAMP(6)),
('LENDER', CURRENT_TIMESTAMP(6), CURRENT_TIMESTAMP(6)),
('ADMIN', CURRENT_TIMESTAMP(6), CURRENT_TIMESTAMP(6));
