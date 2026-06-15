package com.matalcross.webtoon.controller;

import com.matalcross.webtoon.dto.EpisodeItem;
import com.matalcross.webtoon.dto.WebtoonItem;
import com.matalcross.webtoon.entity.User;
import com.matalcross.webtoon.entity.UserOAuthAccount;
import com.matalcross.webtoon.service.UserService;
import com.matalcross.webtoon.service.WebtoonService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Controller
@RequiredArgsConstructor
public class WebtoonController {

    private final WebtoonService webtoonService;
    private final UserService userService;

    @GetMapping("/")
    public String home(Model model) {
        List<WebtoonItem> webtoons = webtoonService.getTodayWebtoons();
        model.addAttribute("hero", webtoons.isEmpty() ? null : webtoons.get(0));
        model.addAttribute("webtoons", webtoons);
        return "webtoon/home";
    }

    @GetMapping("/webtoon/{id}")
    public String webtoonList(@PathVariable String id, Model model) {
        WebtoonItem webtoon = webtoonService.getWebtoonById(id);
        List<EpisodeItem> episodes = webtoonService.getEpisodes(id);
        model.addAttribute("webtoon", webtoon);
        model.addAttribute("webtoonId", id);
        model.addAttribute("episodes", episodes);
        return "webtoon/webtoon_list";
    }

    @GetMapping("/search")
    public String search() {
        return "webtoon/search";
    }

    @GetMapping("/storage")
    public String storage() {
        return "webtoon/storage";
    }

    @GetMapping("/mypage")
    public String mypage(Model model, @AuthenticationPrincipal OAuth2User principal) {
        if (principal != null) {
            String email = principal.getAttribute("email");
            User userProfile = userService.getUserByEmail(email);
            java.util.List<UserOAuthAccount> oauthAccounts = userService.getOAuthAccounts(userProfile);
            model.addAttribute("userProfile", userProfile);
            model.addAttribute("oauthAccounts", oauthAccounts);
        }
        return "webtoon/mypage";
    }

    @GetMapping("/weekly")
    public String weekly(Model model) {
        Map<String, List<WebtoonItem>> weeklyWebtoons = webtoonService.getWeeklyWebtoons();

        Map<String, String> dayLabels = new LinkedHashMap<>();
        dayLabels.put("MONDAY",    "월");
        dayLabels.put("TUESDAY",   "화");
        dayLabels.put("WEDNESDAY", "수");
        dayLabels.put("THURSDAY",  "목");
        dayLabels.put("FRIDAY",    "금");
        dayLabels.put("SATURDAY",  "토");
        dayLabels.put("SUNDAY",    "일");

        model.addAttribute("weeklyWebtoons", weeklyWebtoons);
        model.addAttribute("dayLabels", dayLabels);
        model.addAttribute("today", LocalDate.now().getDayOfWeek().name());
        return "webtoon/weekly";
    }

    @GetMapping("/login")
    public String login() {
        return "webtoon/login";
    }
}
