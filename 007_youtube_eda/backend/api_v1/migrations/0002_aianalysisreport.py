from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AiAnalysisReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('summary', models.TextField(verbose_name='AI 종합 요약')),
                ('insights', models.JSONField(verbose_name='AI 인사이트 (JSON)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('channel', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_reports',
                    to='api_v1.channel',
                    verbose_name='채널',
                )),
            ],
            options={
                'verbose_name': 'AI 분석 리포트',
                'verbose_name_plural': 'AI 분석 리포트 목록',
                'db_table': 'ai_analysis_report',
                'ordering': ['-created_at'],
            },
        ),
    ]
