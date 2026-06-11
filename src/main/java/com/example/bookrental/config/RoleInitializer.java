package com.example.bookrental.config;

import com.example.bookrental.domain.Role;
import com.example.bookrental.domain.enums.RoleName;
import com.example.bookrental.repository.RoleRepository;
import java.util.Arrays;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class RoleInitializer implements ApplicationRunner {
    private final RoleRepository roleRepository;
    public RoleInitializer(RoleRepository roleRepository) { this.roleRepository = roleRepository; }
    @Override @Transactional
    public void run(ApplicationArguments args) {
        Arrays.stream(RoleName.values()).filter(role -> roleRepository.findByName(role).isEmpty())
                .forEach(role -> roleRepository.save(new Role(role)));
    }
}
