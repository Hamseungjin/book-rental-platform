package com.example.bookrental.domain;

import com.example.bookrental.domain.enums.RoleName;
import jakarta.persistence.*;

@Entity
@Table(name = "roles", uniqueConstraints = @UniqueConstraint(name = "uk_roles_name", columnNames = "name"))
public class Role extends BaseEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Enumerated(EnumType.STRING) @Column(nullable = false, length = 30)
    private RoleName name;

    protected Role() {}
    public Role(RoleName name) { this.name = name; }
    public Long getId() { return id; }
    public RoleName getName() { return name; }
}
