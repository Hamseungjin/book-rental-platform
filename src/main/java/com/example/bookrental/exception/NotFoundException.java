package com.example.bookrental.exception;
public class NotFoundException extends RuntimeException {
    public NotFoundException(String resource, Long id) { super(resource + "을(를) 찾을 수 없습니다. id=" + id); }
}
