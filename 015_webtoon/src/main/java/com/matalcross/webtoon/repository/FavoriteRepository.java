package com.matalcross.webtoon.repository;

import com.matalcross.webtoon.entity.Favorite;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FavoriteRepository extends JpaRepository<Favorite, Favorite.FavoritePK> {
    long countByWebtoonId(Long webtoonId);
}
