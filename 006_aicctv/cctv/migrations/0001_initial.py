from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('name_en', models.CharField(blank=True, max_length=100)),
                ('department', models.CharField(max_length=100)),
                ('role', models.CharField(blank=True, max_length=100)),
                ('access_level', models.PositiveSmallIntegerField(default=1)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='employees/')),
            ],
        ),
        migrations.CreateModel(
            name='AccessLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('direction', models.CharField(choices=[('IN', '입장'), ('OUT', '퇴장')], max_length=3)),
                ('match_confidence', models.FloatField()),
                ('distance', models.FloatField(default=0.0)),
                ('encoder', models.CharField(default='dlib_128', max_length=50)),
                ('status', models.CharField(choices=[('GRANTED', '허가'), ('DENIED', '거부')], max_length=10)),
                ('employee', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='access_logs',
                    to='cctv.employee',
                )),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
