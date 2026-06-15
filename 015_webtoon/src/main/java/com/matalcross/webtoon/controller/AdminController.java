package com.matalcross.webtoon.controller;

import com.matalcross.webtoon.entity.Episode;
import com.matalcross.webtoon.entity.User;
import com.matalcross.webtoon.entity.Webtoon;
import com.matalcross.webtoon.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Controller
@RequestMapping("/admin")
@RequiredArgsConstructor
public class AdminController {

    private final WebtoonRepository webtoonRepository;
    private final UserRepository userRepository;
    private final EpisodeRepository episodeRepository;
    private final FavoriteRepository favoriteRepository;
    private final EpisodeReadRepository episodeReadRepository;
    private final CommentRepository commentRepository;

    @GetMapping
    public String dashboard(Model model) {
        model.addAttribute("totalWebtoons", webtoonRepository.count());
        model.addAttribute("totalUsers",    userRepository.count());
        model.addAttribute("totalEpisodes", episodeRepository.count());

        List<User>    recentUsers    = userRepository.findAllByOrderByCreatedAtDesc();
        List<Webtoon> recentWebtoons = webtoonRepository.findAllByOrderByCreatedAtDesc();
        model.addAttribute("recentUsers",    recentUsers.stream().limit(5).toList());
        model.addAttribute("recentWebtoons", recentWebtoons.stream().limit(5).toList());
        return "admin/dashboard";
    }

    @GetMapping("/login")
    public String loginPage() {
        return "admin/admin_login";
    }

    @GetMapping("/member_list")
    public String memberList(Model model) {
        model.addAttribute("members", userRepository.findAllByOrderByCreatedAtDesc());
        return "admin/member_list";
    }

    @GetMapping("/webtoon_list")
    public String webtoonList(Model model) {
        model.addAttribute("webtoons", webtoonRepository.findAllByOrderByCreatedAtDesc());
        return "admin/webtoon_list";
    }

    @GetMapping("/webtoon_view/{id}")
    public String webtoonView(@PathVariable Long id, Model model) {
        Webtoon webtoon = webtoonRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("웹툰 없음: " + id));

        List<Episode> episodes = episodeRepository.findByWebtoon_IdOrderByIdAsc(id);

        // 통계 집계
        long favoriteCount  = favoriteRepository.countByWebtoonId(id);
        List<Long> episodeIds = episodes.stream().map(Episode::getId).toList();
        long totalReads    = episodeIds.isEmpty() ? 0 : episodeReadRepository.countByEpisodeIdIn(episodeIds);
        long totalComments = episodeIds.isEmpty() ? 0 : commentRepository.countByEpisodeIdInAndDeletedAtIsNull(episodeIds);

        // 에피소드별 조회수·댓글 수 Map
        Map<Long, Long> readCountMap    = new HashMap<>();
        Map<Long, Long> commentCountMap = new HashMap<>();
        if (!episodeIds.isEmpty()) {
            episodeReadRepository.countGroupByEpisodeId(episodeIds)
                    .forEach(row -> readCountMap.put((Long) row[0], (Long) row[1]));
            commentRepository.countGroupByEpisodeId(episodeIds)
                    .forEach(row -> commentCountMap.put((Long) row[0], (Long) row[1]));
        }

        // Chart.js 데이터 (최대 30화)
        int chartSize = Math.min(episodes.size(), 30);
        List<String>     chartLabels  = new ArrayList<>();
        List<BigDecimal> chartRatings = new ArrayList<>();
        List<Long>       chartReads   = new ArrayList<>();

        for (int i = 0; i < chartSize; i++) {
            Episode ep = episodes.get(i);
            chartLabels.add((i + 1) + "화");
            chartRatings.add(ep.getRating() != null ? ep.getRating() : BigDecimal.ZERO);
            chartReads.add(readCountMap.getOrDefault(ep.getId(), 0L));
        }

        model.addAttribute("webtoon",         webtoon);
        model.addAttribute("episodes",         episodes);
        model.addAttribute("favoriteCount",    favoriteCount);
        model.addAttribute("totalReads",       totalReads);
        model.addAttribute("totalComments",    totalComments);
        model.addAttribute("readCountMap",     readCountMap);
        model.addAttribute("commentCountMap",  commentCountMap);
        model.addAttribute("chartLabels",      chartLabels);
        model.addAttribute("chartRatings",     chartRatings);
        model.addAttribute("chartReads",       chartReads);

        return "admin/webtoon_view";
    }
}
