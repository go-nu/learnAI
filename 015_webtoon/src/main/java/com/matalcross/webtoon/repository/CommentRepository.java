package com.matalcross.webtoon.repository;

import com.matalcross.webtoon.entity.Comment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface CommentRepository extends JpaRepository<Comment, Long> {
    long countByEpisodeIdInAndDeletedAtIsNull(List<Long> episodeIds);

    @Query("SELECT c.episodeId, COUNT(c) FROM Comment c WHERE c.episodeId IN :ids AND c.deletedAt IS NULL GROUP BY c.episodeId")
    List<Object[]> countGroupByEpisodeId(@Param("ids") List<Long> ids);
}
