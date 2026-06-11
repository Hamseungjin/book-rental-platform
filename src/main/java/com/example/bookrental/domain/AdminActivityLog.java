package com.example.bookrental.domain;

import com.example.bookrental.domain.enums.AdminAction;
import com.example.bookrental.domain.enums.AdminTargetType;
import jakarta.persistence.*;

@Entity
@Table(name = "admin_activity_logs", indexes = @Index(name = "idx_admin_logs_admin_created", columnList = "admin_id,created_at"))
public class AdminActivityLog extends BaseEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "admin_id", nullable = false, foreignKey = @ForeignKey(name = "fk_admin_logs_admin"))
    private User admin;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 50)
    private AdminAction action;
    @Enumerated(EnumType.STRING) @Column(name = "target_type", nullable = false, length = 50)
    private AdminTargetType targetType;
    @Column(name = "target_id", nullable = false)
    private Long targetId;
    @Column(length = 1000)
    private String memo;

    protected AdminActivityLog() {}
    public AdminActivityLog(User admin, AdminAction action, AdminTargetType targetType, Long targetId, String memo) {
        this.admin = admin; this.action = action; this.targetType = targetType; this.targetId = targetId; this.memo = memo;
    }
    public Long getId() { return id; }
    public User getAdmin() { return admin; }
    public AdminAction getAction() { return action; }
    public AdminTargetType getTargetType() { return targetType; }
    public Long getTargetId() { return targetId; }
    public String getMemo() { return memo; }
}
