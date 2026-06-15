package com.matalcross.webtoon.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "episodes", uniqueConstraints = {
        @UniqueConstraint(name = "uq_episodes_webtoon_source", columnNames = {"webtoon_id", "source_id"})
})
@Getter
@Setter
@NoArgsConstructor
public class Episode {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "webtoon_id", nullable = false)
    private Webtoon webtoon;

    @Column(name = "source_id", nullable = false, length = 50)
    private String sourceId;

    @Column(nullable = false, length = 255)
    private String title;

    @Column(precision = 4, scale = 2)
    private BigDecimal rating;

    @Column(name = "published_date", length = 50)
    private String publishedDate;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
