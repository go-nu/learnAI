package com.matalcross.webtoon.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

@Entity
@Table(name = "favorites")
@IdClass(Favorite.FavoritePK.class)
@Getter
@NoArgsConstructor
public class Favorite {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @Id
    @Column(name = "webtoon_id")
    private Long webtoonId;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Getter
    @NoArgsConstructor
    public static class FavoritePK implements Serializable {
        private Long userId;
        private Long webtoonId;
    }
}
