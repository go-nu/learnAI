package com.matalcross.webtoon.service;

import com.matalcross.webtoon.entity.User;
import com.matalcross.webtoon.entity.UserOAuthAccount;
import com.matalcross.webtoon.repository.UserOAuthAccountRepository;
import com.matalcross.webtoon.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final UserOAuthAccountRepository userOAuthAccountRepository;

    @Transactional(readOnly = true)
    public User getUserByEmail(String email) {
        if (email == null) return null;
        return userRepository.findByEmail(email).orElse(null);
    }

    @Transactional(readOnly = true)
    public List<UserOAuthAccount> getOAuthAccounts(User user) {
        if (user == null) return List.of();
        return userOAuthAccountRepository.findByUserId(user.getId());
    }
}
