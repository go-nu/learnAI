package com.matalcross.webtoon.oauth;

import com.matalcross.webtoon.entity.User;
import com.matalcross.webtoon.entity.UserOAuthAccount;
import com.matalcross.webtoon.repository.UserOAuthAccountRepository;
import com.matalcross.webtoon.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;
    private final UserOAuthAccountRepository userOAuthAccountRepository;

    @Override
    @Transactional
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);

        String provider = userRequest.getClientRegistration().getRegistrationId(); // "google"
        String providerUserId = oAuth2User.getAttribute("sub");
        String email = oAuth2User.getAttribute("email");
        String name = oAuth2User.getAttribute("name");
        String picture = oAuth2User.getAttribute("picture");
        Boolean emailVerified = oAuth2User.getAttribute("email_verified");

        UserOAuthAccount oauthAccount = userOAuthAccountRepository
                .findByProviderAndProviderUserId(provider, providerUserId)
                .orElse(null);

        User user;
        if (oauthAccount != null) {
            // 기존 사용자 — 마지막 로그인 시각 갱신
            user = oauthAccount.getUser();
            user.setLastLoginAt(LocalDateTime.now());
            if (picture != null) user.setProfileImageUrl(picture);
            userRepository.save(user);
        } else {
            // 신규 OAuth 연동 — 이메일로 기존 계정 조회 또는 신규 생성
            user = userRepository.findByEmail(email).orElse(null);
            if (user == null) {
                user = new User();
                user.setEmail(email);
                user.setNickname(uniqueNickname(name));
                user.setProfileImageUrl(picture);
                user.setStatus(User.Status.active);
                if (Boolean.TRUE.equals(emailVerified)) {
                    user.setEmailVerifiedAt(LocalDateTime.now());
                }
            }
            user.setLastLoginAt(LocalDateTime.now());
            if (picture != null) user.setProfileImageUrl(picture);
            userRepository.save(user);

            UserOAuthAccount account = new UserOAuthAccount();
            account.setUser(user);
            account.setProvider(provider);
            account.setProviderUserId(providerUserId);
            userOAuthAccountRepository.save(account);
        }

        return oAuth2User;
    }

    private String uniqueNickname(String base) {
        String candidate = (base != null && !base.isBlank())
                ? base.replaceAll("\\s+", "_")
                : "user";
        if (candidate.length() > 40) candidate = candidate.substring(0, 40);
        if (!userRepository.existsByNickname(candidate)) return candidate;
        String result;
        do {
            String suffix = UUID.randomUUID().toString().substring(0, 4);
            String trimmed = candidate.length() > 45 ? candidate.substring(0, 45) : candidate;
            result = trimmed + "_" + suffix;
        } while (userRepository.existsByNickname(result));
        return result;
    }
}
