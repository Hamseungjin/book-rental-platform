package com.example.bookrental.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "user_roles", uniqueConstraints = @UniqueConstraint(name = "uk_user_roles", columnNames = {"user_id", "role_id"}))
public class UserRole extends BaseEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false, foreignKey = @ForeignKey(name = "fk_user_roles_user"))
    private User user;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "role_id", nullable = false, foreignKey = @ForeignKey(name = "fk_user_roles_role"))
    private Role role;

    protected UserRole() {}
    public UserRole(User user, Role role) { this.user = user; this.role = role; }
    public Long getId() { return id; }
    public User getUser() { return user; }
    public Role getRole() { return role; }
}
