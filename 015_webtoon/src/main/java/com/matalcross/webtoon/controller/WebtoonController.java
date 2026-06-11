package com.matalcross.webtoon.controller;

import com.matalcross.webtoon.dto.WebtoonItem;
import com.matalcross.webtoon.service.WebtoonService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
@RequiredArgsConstructor
public class WebtoonController {

    private final WebtoonService webtoonService;

    @GetMapping("/")
    public String home(Model model) {
        List<WebtoonItem> webtoons = webtoonService.getTodayWebtoons();
        model.addAttribute("hero", webtoons.isEmpty() ? null : webtoons.get(0));
        model.addAttribute("webtoons", webtoons);
        return "webtoon/home";
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
    public String mypage() {
        return "webtoon/mypage";
    }

    @GetMapping("/weekly")
    public String weekly() {
        return "webtoon/weekly";
    }
}
