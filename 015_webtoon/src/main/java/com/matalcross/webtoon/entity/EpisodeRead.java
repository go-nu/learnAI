package com.matalcross.webtoon.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

@Entity
@Table(name = "episode_reads")
@IdClass(EpisodeRead.EpisodeReadPK.class)
@Getter
@NoArgsConstructor
public class EpisodeRead {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @Id
    @Column(name = "episode_id")
    private Long episodeId;

    @Column(name = "read_at")
    private LocalDateTime readAt;

    @Getter
    @NoArgsConstructor
    public static class EpisodeReadPK implements Serializable {
        private Long userId;
        private Long episodeId;
    }
}
