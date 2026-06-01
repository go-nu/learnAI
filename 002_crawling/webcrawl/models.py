from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=255)
    ko_tilte = models.CharField(max_length=255, default="", null=True)
    year = models.CharField(max_length=10)
    rated = models.CharField(max_length=20, blank=True, null=True)
    released = models.CharField(max_length=50, blank=True, null=True)
    runtime = models.CharField(max_length=20, blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True)
    director = models.CharField(max_length=255, blank=True, null=True)
    writer = models.TextField(blank=True, null=True)
    actors = models.TextField(blank=True, null=True)
    plot = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    awards = models.TextField(blank=True, null=True)
    poster = models.URLField(max_length=500, blank=True, null=True)

    # Ratings
    ratings1_source = models.CharField(max_length=100, blank=True, null=True)
    ratings1_value = models.CharField(max_length=20, blank=True, null=True)
    ratings2_source = models.CharField(max_length=100, blank=True, null=True)
    ratings2_value = models.CharField(max_length=20, blank=True, null=True)

    # Scores
    metascore = models.CharField(max_length=10, blank=True, null=True)
    imdb_rating = models.CharField(max_length=10, blank=True, null=True)
    imdb_votes = models.CharField(max_length=20, blank=True, null=True)
    imdb_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # Distribution
    type = models.CharField(max_length=50, blank=True, null=True)
    dvd = models.CharField(max_length=50, blank=True, null=True)
    box_office = models.CharField(max_length=50, blank=True, null=True)
    production = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(max_length=500, blank=True, null=True)
    response = models.CharField(max_length=10, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movie"
        verbose_name = "Movie"
        verbose_name_plural = "Movies"

    def __str__(self):
        return f"{self.ko_tilte}({self.title}) ({self.year})"