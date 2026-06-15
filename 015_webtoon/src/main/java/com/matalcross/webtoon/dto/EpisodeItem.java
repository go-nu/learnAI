package com.matalcross.webtoon.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.math.BigDecimal;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class EpisodeItem {
    private String id;
    private String title;
    private String thumb;
    private String date;
    private BigDecimal rating;
}
