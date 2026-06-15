package com.matalcross.webtoon.repository;

import com.matalcross.webtoon.entity.Webtoon;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface WebtoonRepository extends JpaRepository<Webtoon, Long> {
    boolean existsBySourceId(String sourceId);
    Optional<Webtoon> findBySourceId(String sourceId);
    List<Webtoon> findAllByOrderByCreatedAtDesc();
}
