from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='name_en',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='manager',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='managers/'),
        ),
    ]
