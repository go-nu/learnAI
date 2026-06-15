package com.matalcross.webtoon.service;

import com.matalcross.webtoon.dto.EpisodeItem;
import com.matalcross.webtoon.dto.WebtoonItem;
import com.matalcross.webtoon.entity.Episode;
import com.matalcross.webtoon.entity.Webtoon;
import com.matalcross.webtoon.repository.EpisodeRepository;
import com.matalcross.webtoon.repository.WebtoonRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class WebtoonService {

    private static final String BASE_API = "https://webtoon-crawler.nomadcoders.workers.dev";

    private final RestTemplate restTemplate;
    private final WebtoonRepository webtoonRepository;
    private final EpisodeRepository episodeRepository;

    @Transactional
    public List<WebtoonItem> getTodayWebtoons() {
        // 1. API에서 오늘의 웹툰을 가져와 신규 웹툰 DB 저장
        WebtoonItem[] apiItems = restTemplate.getForObject(BASE_API + "/today", WebtoonItem[].class);
        if (apiItems != null) {
            for (WebtoonItem item : apiItems) {
                saveWebtoonIfAbsent(item);
            }
        }

        // 2. DB에 저장된 모든 웹툰 중 에피소드 없는 것만 API 호출 후 저장
        for (Webtoon webtoon : webtoonRepository.findAll()) {
            saveEpisodesIfAbsent(webtoon);
        }

        // 3. DB에서 최신 저장순으로 조회 후 반환 (첫 번째 = hero)
        return webtoonRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(this::toWebtoonItem)
                .collect(Collectors.toList());
    }

    private WebtoonItem toWebtoonItem(Webtoon webtoon) {
        WebtoonItem item = new WebtoonItem();
        item.setId(webtoon.getSourceId());
        item.setTitle(webtoon.getTitle());
        item.setThumb(webtoon.getThumbUrl());
        return item;
    }

    // 신규 웹툰이면 저장, 기존이면 DB 엔티티 반환
    private Webtoon saveWebtoonIfAbsent(WebtoonItem item) {
        return webtoonRepository.findBySourceId(item.getId())
                .orElseGet(() -> {
                    Webtoon w = new Webtoon();
                    w.setSourceId(item.getId());
                    w.setTitle(item.getTitle());
                    w.setThumbUrl(item.getThumb());
                    w.setToday(true);
                    return webtoonRepository.save(w);
                });
    }

    // 에피소드가 없는 웹툰만 API 호출 후 전체 저장 (중복 방지)
    private void saveEpisodesIfAbsent(Webtoon webtoon) {
        if (episodeRepository.existsByWebtoonId(webtoon.getId())) return;

        EpisodeItem[] items = restTemplate.getForObject(
                BASE_API + "/" + webtoon.getSourceId() + "/episodes", EpisodeItem[].class);
        if (items == null) return;

        for (EpisodeItem ep : items) {
            Episode episode = new Episode();
            episode.setWebtoon(webtoon);
            episode.setSourceId(ep.getId());
            episode.setTitle(ep.getTitle());
            episode.setRating(ep.getRating());
            episode.setPublishedDate(ep.getDate());
            episodeRepository.save(episode);
        }
    }

    public Map<String, List<WebtoonItem>> getWeeklyWebtoons() {
        Map<String, List<WebtoonItem>> result = new LinkedHashMap<>();
        for (String day : Arrays.asList("MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY")) {
            result.put(day, new ArrayList<>());
        }
        for (Webtoon w : webtoonRepository.findAllByOrderByCreatedAtDesc()) {
            if (w.getCreatedAt() != null) {
                String day = w.getCreatedAt().getDayOfWeek().name();
                List<WebtoonItem> list = result.get(day);
                if (list != null) list.add(toWebtoonItem(w));
            }
        }
        return result;
    }

    public WebtoonItem getWebtoonById(String id) {
        return restTemplate.getForObject(BASE_API + "/" + id, WebtoonItem.class);
    }

    public List<EpisodeItem> getEpisodes(String id) {
        EpisodeItem[] items = restTemplate.getForObject(BASE_API + "/" + id + "/episodes", EpisodeItem[].class);
        if (items == null) return Collections.emptyList();
        return Arrays.asList(items);
    }
}