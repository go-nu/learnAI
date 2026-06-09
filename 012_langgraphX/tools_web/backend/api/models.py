from django.db import models


class GenerationRecord(models.Model):
    MODE_CHOICES = [('text2img', 'Text to Image'), ('img2img', 'Image to Image')]

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='text2img')
    prompt = models.TextField()
    denoise = models.FloatField(default=0.75)
    result_image = models.CharField(max_length=500, blank=True)
    input_image = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.mode}] {self.prompt[:50]}"
