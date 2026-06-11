package com.example.bookrental.exception;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<ApiErrorResponse> notFound(NotFoundException e) { return response(HttpStatus.NOT_FOUND, "NOT_FOUND", e.getMessage(), Map.of()); }
    @ExceptionHandler(ForbiddenException.class)
    public ResponseEntity<ApiErrorResponse> forbidden(ForbiddenException e) { return response(HttpStatus.FORBIDDEN, "FORBIDDEN", e.getMessage(), Map.of()); }
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiErrorResponse> business(BusinessException e) { return response(HttpStatus.CONFLICT, "BUSINESS_RULE_VIOLATION", e.getMessage(), Map.of()); }
    @ExceptionHandler({MissingRequestHeaderException.class, HttpMessageNotReadableException.class})
    public ResponseEntity<ApiErrorResponse> malformedRequest(Exception e) {
        return response(HttpStatus.BAD_REQUEST, "MALFORMED_REQUEST", "요청 헤더 또는 본문 형식이 올바르지 않습니다.", Map.of());
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiErrorResponse> validation(MethodArgumentNotValidException e) {
        Map<String, String> fields = new LinkedHashMap<>();
        for (FieldError error : e.getBindingResult().getFieldErrors()) fields.putIfAbsent(error.getField(), error.getDefaultMessage());
        return response(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "요청 값이 올바르지 않습니다.", fields);
    }
    private ResponseEntity<ApiErrorResponse> response(HttpStatus status, String code, String message, Map<String, String> fields) {
        return ResponseEntity.status(status).body(new ApiErrorResponse(LocalDateTime.now(), status.value(), code, message, fields));
    }
}
