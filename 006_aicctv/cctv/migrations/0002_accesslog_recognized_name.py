from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cctv', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesslog',
            name='recognized_name',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
