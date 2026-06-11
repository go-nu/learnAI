package com.matalcross.webtoon.service;

import com.matalcross.webtoon.dto.WebtoonItem;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

@Service
@RequiredArgsConstructor
public class WebtoonService {

    private static final String TODAY_API = "https://webtoon-crawler.nomadcoders.workers.dev/today";

    private final RestTemplate restTemplate;

    public List<WebtoonItem> getTodayWebtoons() {
        WebtoonItem[] items = restTemplate.getForObject(TODAY_API, WebtoonItem[].class);
        if (items == null) return Collections.emptyList();
        return Arrays.asList(items);
    }
}