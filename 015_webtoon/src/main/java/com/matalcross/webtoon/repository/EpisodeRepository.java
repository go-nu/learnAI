package com.matalcross.webtoon.repository;

import com.matalcross.webtoon.entity.Episode;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface EpisodeRepository extends JpaRepository<Episode, Long> {
    boolean existsByWebtoonId(Long webtoonId);
    List<Episode> findByWebtoon_IdOrderByIdAsc(Long webtoonId);
}
