package com.matalcross.webtoon.repository;

import com.matalcross.webtoon.entity.EpisodeRead;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface EpisodeReadRepository extends JpaRepository<EpisodeRead, EpisodeRead.EpisodeReadPK> {
    long countByEpisodeIdIn(List<Long> episodeIds);

    @Query("SELECT e.episodeId, COUNT(e) FROM EpisodeRead e WHERE e.episodeId IN :ids GROUP BY e.episodeId")
    List<Object[]> countGroupByEpisodeId(@Param("ids") List<Long> ids);
}
