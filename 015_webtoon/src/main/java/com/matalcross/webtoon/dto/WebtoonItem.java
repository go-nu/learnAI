package com.matalcross.webtoon.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class WebtoonItem {
    private String id;
    private String title;
    private String thumb;
}