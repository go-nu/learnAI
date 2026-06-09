from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='GenerationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('text2img', 'Text to Image'), ('img2img', 'Image to Image')], default='text2img', max_length=20)),
                ('prompt', models.TextField()),
                ('denoise', models.FloatField(default=0.75)),
                ('result_image', models.CharField(blank=True, max_length=500)),
                ('input_image', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
